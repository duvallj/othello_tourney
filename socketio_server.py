import socketio
from multiprocessing import Process, Value, Pipe, Event
from collections import deque
import os
import sys
import threading, traceback
import logging as log
import time
import ctypes
import eventlet

from othello_admin import Strategy
import Othello_Core as oc
from run_ai import LocalAI, multiplatform_kill

human_player_name = 'Yourself'
log.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=log.DEBUG)

class GameManagerTemplate(socketio.Server):
    def __init__(self, base_folder, *args, **kw):
        super().__init__(*args, **kw)
        self.possible_names = set()
        self.on('connect', self.create_game)
        self.on('prequest', self.start_game)
        self.on('wrequest', self.watch_game)
        self.on('disconnect', self.delete_game)
        self.on('refresh', self.refresh_game)
        self.on('movereply', self.send_move)
        self.base_folder = base_folder
        self.write_ai()

    def create_game(self, sid, environ): pass
    def start_game(self, sid, data): pass
    def watch_game(self, sid, data): pass
    def delete_game(self, sid): pass
    def refresh_game(self, sid, data): pass
    def send_move(self, sid, data): pass

    def get_possible_files(self):
        possible = []
        for x in os.listdir(os.path.join(self.base_folder, 'students')):
            try:
                if x != "__pycache__" and os.path.isfile(os.path.join(self.base_folder, 'students', x, 'strategy.py')):
                    possible.append('students.{}.strategy'.format(x))
            except:
                traceback.print_exc()
                pass
        return possible

    def write_ai(self):
        self.possible_names = set()
        files = self.get_possible_files()
        buf = ''
        
        for x in range(len(files)):
            name = files[x].split('.')[1]
            self.possible_names.add(name)
            buf += name +'\n'
            
        log.info('All strategies read')


class GameForwarder(GameManagerTemplate):
    incoming = ['prequest', 'wrequest', 'refresh', 'movereply']
    outgoing = ['reply', 'moverequest', 'gameend']
    
    def __init__(self, host_list, *args, **kw):
        import random
        from socketIO_client import SocketIO, LoggingNamespace
        super().__init__(*args, **kw)
        self.host_list = host_list
        self.sessions = dict()
        self.sprocs = dict()
        self.spipes = dict()
        for mtype in self.incoming:
            self.create_forward_in(mtype)

    def create_forward_in(self, mtype):
        def inner_forward_in(sid, data):
            sess = self.sessions.get(sid, None)
            if sess is not None:
                log.debug("Callback forwarding in {} to {}".format(mtype, sid))
                sess.emit(mtype, data)
            else:
                log.warn("SID {} does not exist!".format(sid))
        self.on(mtype, inner_forward_in)

    def create_forward_out(self, mtype, sid):
        def inner_forward_out(data):
            log.debug("Callback forwarding out {} to {}".format(mtype, sid))
            self.emit(mtype, data=data, room=sid)
        self.sessions[sid].on(mtype, inner_forward_out)

    def create_game(self, sid, environ):
        target_host, target_port = random.choice(self.host_list)
        self.sessions[sid] = SocketIO(target_host, target_port, LoggingNamespace)
        for mtype in self.outgoing:
            self.create_forward_out(mtype, sid)
        self.sprocs[sid] = eventlet.spawn(self.sessions[sid].wait)
            
    def delete_game(self, sid):
        if sid in self.sessions:
            self.sprocs[sid].kill()
            self.sessions[sid].disconnect()
            del self.sessions[sid]
            del self.sprocs[sid]
            
            
class GameData:
    def __init__(self, game=None, pipe=None, proc=None, bgproc=None, bglock=None, bgrun=False, kill_event=None, done_event=None):
        self.game = game
        self.pipe = pipe
        self.proc = proc
        self.bgproc = bgproc
        self.bglock = bglock
        self.bgrun = bgrun
        self.kill_event = kill_event
        self.done_event = done_event
        

class GameManager(GameManagerTemplate):
    def __init__(self, *args, remotes=None, jail_begin=None, **kw):
        super().__init__(*args, **kw)
        self.cdata = dict()
        self.remotes = remotes
        self.jail_begin = jail_begin
        
    def create_game(self, sid, environ):
        log.info('Client '+sid+' connected')
        self.cdata[sid] = GameData(game=GameRunner(self.possible_names, self.remotes, jail_begin=self.jail_begin))

    def start_game(self, sid, data):
        log.info('Client '+sid+' requests game '+str(data))
        cdata = self.cdata[sid]
        
        try:
            timelimit = min(float(data['tml']), 60)
        except ValueError:
            timelimit = 5
            
        cdata.game.post_init(data['black'].strip(), data['white'].strip(), timelimit)
        
        parent_conn, child_conn = Pipe()
        cdata.pipe = parent_conn
        
        cdata.kill_event = Event()
        cdata.done_event = Event()
        
        cdata.proc = Process(target=cdata.game.run_game, args=(child_conn, cdata.kill_event, cdata.done_event))
        cdata.proc.start()
        
        """
        cdata.bglock = threading.Lock()
        cdata.bgrun = True
        
        def _bg_refresh():
            cdata.bglock.acquire()
            while cdata.bgrun:
                cdata.bglock.release()
                self.refresh_game(sid, None)
                cdata.bglock.acquire()
            cdata.bglock.release()
        
        cdata.bgproc = threading.Thread(target=_bg_refresh)
        cdata.bgproc.start()
        """
        
        def _bg_refresh():
            while True:
                try:
                    self.refresh_game(sid, None)
                except:
                    log.debug(traceback.format_exc())
                eventlet.sleep(0.1)
        cdata.bgproc = eventlet.spawn(_bg_refresh)
        
        log.debug('Started game for '+sid)
        
    def watch_game(self, sid, data):
        log.debug("Client "+sid+" requests to watch a game "+data.get('watching', sid))
        self.enter_room(sid, data.get('watching', sid))

    def delete_game(self, sid):
        log.info('Client '+sid+' disconnected')
        
        cdata = None
        if sid in self.cdata:
            cdata = self.cdata[sid]
        else:
            return
            
        try:
            if cdata.proc.is_alive():
                cdata.kill_event.set()
                log.debug("{} kill event set".format(sid))
                cdata.done_event.wait(timeout=60)
                log.debug("{} should be done now".format(sid))
                if cdata.proc.is_alive(): cdata.proc.terminate()
            #del cdata.proc
        except: pass
        
        try:
            #with cdata.bglock:
            #    cdata.bgrun = False
            #cdata.bgproc.join()
            cdata.bgproc.kill()
            self.refresh_game(sid, None)
            #del cdata.bgproc
        except: pass
        
        del self.cdata[sid]
        del cdata

    def refresh_game(self, sid, data):
        cdata = self.cdata.get(sid, False)
        
        if cdata:
            closed = cdata.pipe.closed
            msgq = deque()
            
            if not closed:
                try:
                    while cdata.pipe.poll():
                        packet = cdata.pipe.recv()
                        msgq.append(packet)
                        
                except (BrokenPipeError, EOFError):
                    log.debug('Pipe is broken, closing...')
                    cdata.pipe.close()
                
            while msgq:
                self.act_on_message(sid, msgq.popleft())
        else:
            log.debug('Telling client '+sid+' the game is no longer going on...')
            self.emit('gameend', data={'winner':oc.OUTER, 'forfeit':True, 'error_msg': None, 'black_score': 0}, room=sid)

    def act_on_message(self, sid, packet):
        mtype, data = packet
        log.debug("{} got packet ({}, {})".format(sid, mtype, data))
        if mtype == 'board':
            self.emit('reply', data=data, room=sid)
        elif mtype == 'getmove':
            self.emit('moverequest', data=dict(), room=sid)
        elif mtype == 'gameend':
            self.emit('gameend', data=data, room=sid)

    def send_move(self, sid, data):
        if sid in self.cdata:
            move = int(data['move'])
            self.cdata[sid].pipe.send(move)
            log.info('Recieved move '+str(move)+' from '+sid)

class GameRunner:
    AIClass = LocalAI
    def __init__(self, possible_names, remotes=None, jail_begin=None):
        self.core = Strategy()
        self.possible_names = possible_names
        self.remotes = remotes
        self.jail_begin = jail_begin
        if self.remotes:
            from run_ai_remote import RemoteAI
            self.AIClass = RemoteAI
        elif self.jail_begin:
            from run_ai_jailed import JailedAI
            self.AIClass = JailedAI
        self.timelimit = 5
        self.BLACK = None
        self.WHITE = None
        self.playing = False
        

    def post_init(self, nameA, nameB, timelimit):
        self.BLACK = nameA if nameA in self.possible_names else None
        self.WHITE = nameB if nameB in self.possible_names else None
        self.BLACK_NAME = self.BLACK if self.BLACK else human_player_name
        self.WHITE_NAME = self.WHITE if self.WHITE else human_player_name
        self.timelimit = timelimit
        self.playing = True
        log.debug('Set names to '+str(self.BLACK)+' '+str(self.WHITE))

    def run_game(self, conn, kill_event, done_event):
        log.debug('Game process creation sucessful')
        board = self.core.initial_board()
        player = oc.BLACK
        black_score = 0
        
        try:
            self.BLACK_STRAT = self.AIClass(self.BLACK, self.possible_names, \
            self.remotes, jail_begin=self.jail_begin)
        except:
            self.BLACK_STRAT = None
            black_score -= 100
        try:
            self.WHITE_STRAT = self.AIClass(self.WHITE, self.possible_names, \
            self.remotes, jail_begin=self.jail_begin)
        except:
            self.WHITE_STRAT = None
            black_score += 100

        if self.BLACK_STRAT is None or self.WHITE_STRAT is None:
            winner = (oc.WHITE, oc.EMPTY, oc.BLACK)[(black_score>0)-(black_score<0)+1]
            conn.send((
                'gameend',
                {
                    'winner': winner,
                    'forfeit': True,
                    'err_msg': None,
                    'black': name_strings[oc.BLACK],
                    'white': name_strings[oc.WHITE],
                    'black_score': black_score
                }
            ))
            done_event.set()
            return
        
        strategy = {oc.BLACK: self.BLACK_STRAT, oc.WHITE: self.WHITE_STRAT}
        names = {oc.BLACK: self.BLACK, oc.WHITE: self.WHITE}
        name_strings = {
            oc.BLACK: self.BLACK_NAME,
            oc.WHITE: self.WHITE_NAME
        }
        conn.send((
            'board',
            {
                'bSize':'8',
                'board':''.join(board),
                'black': name_strings[oc.BLACK],
                'white': name_strings[oc.WHITE],
                'tomove':player
            }
        ))

        forfeit = False
        err_msg = None
        black_score = 0

        while not (player is None or forfeit or kill_event.is_set()):
            log.debug('Main loop!')
            if names[player] is None:
                move = -1
                
                # clear out queue from moves sent by rouge client
                while conn.poll(): temp=conn.recv()
                
                while not self.core.is_legal(move, player, board):
                    conn.send(('getmove', 0))
                    should_break = False
                    
                    while not conn.poll():
                        if kill_event.is_set():
                            should_break = True
                            break
                    
                    if should_break: break
                    move = conn.recv()
                    log.debug('Game recieved move '+str(move))

                log.debug('Move '+str(move)+' determined legal')
            else:
                dat = strategy[player].get_move(''.join(board), player, self.timelimit, kill_event)
                if isinstance(dat, tuple):
                    move, err_msg = dat
                    log.debug(err_msg)
                else:
                    move = dat
            log.debug('Actually got move')
            if not self.core.is_legal(move, player, board):
                forfeit = True
                err_msg = "Invalid Move by {}: {}\nBoard: {}".format(name_strings[[oc.BLACK, oc.WHITE][player == 'o']], move, ''.join(board)) if not err_msg else err_msg
                if player == oc.BLACK:
                    black_score = -100
                else:
                    black_score = 100
                continue

            board = self.core.make_move(move, player, board)
            player = self.core.next_player(board, player)
            black_score = self.core.score(oc.BLACK, board)

            log.debug("\n" + self.core.print_board(board))

            conn.send(('board', {'bSize':'8',
                                 'board':''.join(board),
                                 'black': name_strings[oc.BLACK],
                                 'white': name_strings[oc.WHITE],
                                 'tomove': player if player else oc.BLACK
                                 }
            ))
            log.debug('Sent move out to parent')

        winner = (oc.WHITE, oc.EMPTY, oc.BLACK)[(black_score>0)-(black_score<0)+1]
        log.debug("Winner determined, sending results to parent.")
        conn.send((
            'gameend',
            {
                'winner': winner,
                'forfeit': forfeit,
                'err_msg': err_msg,
                'black': name_strings[oc.BLACK],
                'white': name_strings[oc.WHITE],
                'black_score': black_score
            }
        ))
        done_event.set()
