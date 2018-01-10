import socketio
from socketIO_client import SocketIO, LoggingNamespace
from multiprocessing import Process, Value, Pipe
from collections import deque
import eventlet
import os
import sys
import importlib
import logging as log
import time
import random
import ctypes

from othello_admin import Strategy
import Othello_Core as oc
from run_ai import LocalAI
from run_ai_remote import RemoteAI

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
        folders = os.listdir(os.path.join(self.base_folder, 'students'))
        log.debug('Listed Student folders successfully')
        return ['students.'+x+'.strategy' for x in folders if \
        x != '__pycache__' and \
        os.path.isdir(os.path.join(self.base_folder, 'students', x))]

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

class GameManager(GameManagerTemplate):
    def __init__(self, *args, remotes=None, **kw):
        super().__init__(*args, **kw)
        self.games = dict()
        self.pipes = dict()
        self.procs = dict()
        self.bgprocs = dict()
        self.remotes = remotes
        
    def create_game(self, sid, environ):
        log.info('Client '+sid+' connected')
        self.games[sid] = GameRunner(self.possible_names, self.remotes)

    def start_game(self, sid, data):
        log.info('Client '+sid+' requests game '+str(data))
        
        try:
            timelimit = float(data['tml'])
        except ValueError:
            timelimit = 5
        
        self.games[sid].post_init(data['black'].strip(), data['white'].strip(), timelimit)
        
        parent_conn, child_conn = Pipe()
        self.pipes[sid] = parent_conn
        
        self.procs[sid] = Process(target=self.games[sid].run_game, args=(child_conn,))
        self.procs[sid].start()
        
        def _bg_refresh():
            while True:
                self.refresh_game(sid)
                eventlet.sleep(0)
        self.bgprocs[sid] = eventlet.spawn(_bg_refresh)
        
        log.debug('Started game for '+sid)
        
    def watch_game(self, sid, data):
        self.enter_room(sid, data.get('watching', sid))

    def delete_game(self, sid):
        log.info('Client '+sid+' disconnected')
        try:
            if self.procs[sid].is_alive():
                self.procs[sid].terminate()
            
            del self.procs[sid]
            del self.pipes[sid]
        except:
            pass
        
        del self.games[sid]
        
        try:
            self.bgprocs[sid].kill()
            del self.bgprocs[sid]
        except:
            pass

    def refresh_game(self, sid):
        # no logging
        old_debug = log.debug
        log.debug = lambda *_: None
        # no logging
        
        log.debug('sid: '+str(sid))
        log.debug('Have pipes: '+str(self.pipes))
        exists = sid in self.pipes
        log.debug('Exists: '+str(exists))
        
        if exists:
            log.debug('What is: '+str(self.pipes[sid]))
            closed = self.pipes[sid].closed
            log.debug('Closed: '+str(closed))
            
            msgq = deque()
            
            if not closed:
                try:
                    log.debug('Can poll: '+str(self.pipes[sid].poll()))
                        
                    while self.pipes[sid].poll():
                        packet = self.pipes[sid].recv()
                        msgq.append(packet)
                        
                except (BrokenPipeError, EOFError):
                    log.debug('Pipe is broken, closing...')
                    self.pipes[sid].close()
                
            while msgq:
                self.act_on_message(sid, msgq.popleft())
        else:
            log.debug('Telling client the game is no longer going on...')
            self.emit('gameend', data={'winner':oc.OUTER, 'forfeit':True}, room=osid)
            
        log.debug = old_debug
                
    def act_on_message(self, sid, packet):
        mtype, data = packet
        if mtype == 'board':
            self.emit('reply', data=data, room=sid)
        elif mtype == 'getmove':
            self.emit('moverequest', data=dict(), room=sid)
        elif mtype == 'gameend':
            self.emit('gameend', data=data, room=sid)

    def send_move(self, sid, data):
        move = int(data['move'])
        self.pipes[sid].send(move)
        log.info('Recieved move '+str(move)+' from '+sid)

class GameRunner:
    def __init__(self, possible_names, remotes=None):
        self.core = Strategy()
        self.possible_names = possible_names
        self.remotes = remotes
        if self.remotes:
            self.AI = RemoteAI
        else:
            self.AI = LocalAI
        self.timelimit = 5
        self.BLACK = None
        self.WHITE = None
        self.playing = False
        

    def post_init(self, nameA, nameB, timelimit):
        self.BLACK = nameA if nameA in self.possible_names else None
        self.WHITE = nameB if nameB in self.possible_names else None
        self.timelimit = timelimit
        self.playing = True
        log.debug('Set names to '+str(self.BLACK)+' '+str(self.WHITE))

    def run_game(self, conn):
        log.debug('Game process creation sucessful')
        board = self.core.initial_board()
        player = oc.BLACK
        black_score = 0
        
        try:
            self.BLACK_STRAT = self.AI(self.BLACK, self.possible_names, self.remotes)
        except:
            self.BLACK_STRAT = None
            black_score -= 100
        try:
            self.WHITE_STRAT = self.AI(self.WHITE, self.possible_names, self.remotes)
        except:
            self.WHITE_STRAT = None
            black_score += 100

        if self.BLACK_STRAT is None or self.WHITE_STRAT is None:
            winner = (oc.WHITE, oc.EMPTY, oc.BLACK)[(black_score>0)-(black_score<0)+1]
            conn.send((
                'gameend',
                {
                    'winner': winner,
                    'forfeit': True
                }
            ))
            return
        
        strategy = {oc.BLACK: self.BLACK_STRAT, oc.WHITE: self.WHITE_STRAT}
        names = {oc.BLACK: self.BLACK, oc.WHITE: self.WHITE}
        name_strings = {
            oc.BLACK: self.BLACK if self.BLACK else human_player_name,
            oc.WHITE: self.WHITE if self.WHITE else human_player_name
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
        black_score = 0

        while player is not None and not forfeit:
            log.debug('Main loop!')
            if names[player] is None:
                move = 0
                
                # clear out queue from moves sent by rouge client
                while conn.poll(): temp=conn.recv()
                
                while not self.core.is_legal(move, player, board):
                    conn.send(('getmove', 0))
                    move = conn.recv()
                    log.debug('Game recieved move '+str(move))

                log.debug('Move '+str(move)+' determined legal')
            else:
                move = strategy[player].get_move(''.join(board), player, self.timelimit)
                log.debug('Strategy '+names[player]+' returned move '+str(move))
                
            log.debug('Actually got move')
            if not self.core.is_legal(move, player, board):
                forfeit = True
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
        conn.send((
            'gameend',
            {
                'winner': winner,
                'forfeit': forfeit
            }
        ))
