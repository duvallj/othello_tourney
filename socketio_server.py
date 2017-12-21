import socketio
from socketIO_client import SocketIO, LoggingNamespace
from multiprocessing import Process, Value, Pipe
import eventlet
import os
import sys
import importlib
import logging as log
import time
import random
import ctypes

from othello_admin import *
from run_ai import *

ailist_filename = os.getcwd() + '/static/ai_port_info.txt'
human_player_name = 'Yourself'
log.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=log.DEBUG)

class GameManagerTemplate(socketio.Server):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.possible_names = set()
        self.on('connect', self.create_game)
        self.on('prequest', self.start_game)
        self.on('disconnect', self.delete_game)
        self.on('refresh', self.refresh_game)
        self.on('movereply', self.send_move)

    def create_game(self, sid, environ): pass
    def start_game(self, sid, data): pass
    def delete_game(self, sid): pass
    def refresh_game(self, sid, data): pass
    def send_move(self, sid, data): pass

    def get_possible_files(self):
        folders = os.listdir(os.getcwd()+'/private/Students')
        log.debug('Listed Student folders successfully')
        return ['private.Students.'+x+'.strategy' for x in folders if x != '__pycache__']

    def write_ai(self):
        files = self.get_possible_files()
        buf = ''
        
        for x in range(len(files)):
            name = files[x].split('.')[2]
            self.possible_names.add(name)
            buf += name +'\n'
            
        log.info('All strategies read')
        
        pfile = open(ailist_filename, 'w')
        pfile.write(buf[:-1])
        pfile.close()
        
        log.info('Wrote names to webserver file')
        log.debug('Filename: '+ailist_filename)


class GameForwarder(GameManagerTemplate):
    incoming = ['prequest', 'refresh', 'movereply']
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
                sess.emit(mtype, data)
            else:
                log.warn("SID {} does not exist!".format(sid))
        self.on(mtype, inner_forward_in)

    def create_forward_out(self, mtype, sid):
        def inner_forward_out(data):
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
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.games = dict()
        self.pipes = dict()
        self.procs = dict()
        
    def create_game(self, sid, environ):
        log.info('Client '+sid+' connected')
        self.games[sid] = GameRunner(self.possible_names)

    def start_game(self, sid, data):
        log.info('Client '+sid+' requests game '+str(data))
        parent_conn, child_conn = Pipe()
        if data['tml'].isdigit():
            timelimit = int(data['tml'])
        else:
            timelimit = 5
        self.games[sid].post_init(data['black'].strip(), data['white'].strip(), timelimit)
        self.pipes[sid] = parent_conn
        self.procs[sid] = Process(target=self.games[sid].run_game, args=(child_conn,))
        self.procs[sid].start()
        log.debug('Started game for '+sid)

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

    def refresh_game(self, osid, data):
        if 'watching' in data:
            sid = data['watching']
        else:
            sid = osid
        log.debug('sid: '+str(sid))
        log.debug('Have pipes: '+str(self.pipes))
        exists = sid in self.pipes
        log.debug('Exists: '+str(exists))
        if exists:
            log.debug('What is: '+str(self.pipes[sid]))
            closed = self.pipes[sid].closed
            log.debug('Closed: '+str(closed))
            if not closed:
                try:
                    log.debug('Can poll: '+str(self.pipes[sid].poll()))
                    while self.pipes[sid].poll():
                        mtype, data = self.pipes[sid].recv()
                        if mtype == 'board':
                            self.emit('reply', data=data, room=osid)
                        elif mtype == 'getmove':
                            self.emit('moverequest', data=dict(), room=osid)
                except BrokenPipeError:
                    log.debug('Pipe is broken, closing...')
                    self.pipes[sid].close()
            else:
                log.debug('Telling client the game has ended...')
                self.emit('gameend', data=dict(), room=osid)

    def send_move(self, sid, data):
        move = int(data['move'])
        self.pipes[sid].send(move)
        log.info('Recieved move '+str(move)+' from '+sid)

class GameRunner:
    def __init__(self, possible_names):
        self.core = Strategy()
        self.possible_names = possible_names

    def post_init(self, nameA, nameB, timelimit):
        self.BLACK = nameA if nameA in self.possible_names else None
        self.WHITE = nameB if nameB in self.possible_names else None
        self.BLACK_STRAT = LocalAI(self.BLACK, self.possible_names, timelimit)
        self.WHITE_STRAT = LocalAI(self.WHITE, self.possible_names, timelimit)
        log.debug('Set names to '+str(self.BLACK)+' '+str(self.WHITE))

    def run_game(self, conn):
        log.debug('Game process creation sucessful')
        board = self.core.initial_board()
        player = core.BLACK
        
        strategy = {core.BLACK: self.BLACK_STRAT, core.WHITE: self.WHITE_STRAT}
        names = {core.BLACK: self.BLACK, core.WHITE: self.WHITE}
        conn.send((
            'board',
            {
                'bSize':'8',
                'board':''.join(board),
                'black': self.BLACK if self.BLACK else human_player_name,
                'white': self.WHITE if self.WHITE else human_player_name,
                'tomove':player
            }
        ))

        forfeit = False

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
                move = strategy[player].get_move(''.join(board), player)
                log.debug('Strategy '+names[player]+' returned move '+str(move))
                
            log.debug('Actually got move')
            if not self.core.is_legal(move, player, board):
                forfeit = True
                if player == core.BLACK:
                    black_score = -100
                else:
                    black_score = 100
                continue

            board = self.core.make_move(move, player, board)
            player = self.core.next_player(board, player)
            black_score = self.core.score(core.BLACK, board)

            log.debug(self.core.print_board(board))

            conn.send(('board', {'bSize':'8',
                                 'board':''.join(board),
                                 'black': self.BLACK if self.BLACK else human_player_name,
                                 'white': self.WHITE if self.WHITE else human_player_name,
                                 'tomove': player if player else core.BLACK
                                 }
            ))
            log.debug('Sent move out to parent')

        #self.BLACK_STRAT.kill_remote()
        #self.WHITE_STRAT.kill_remote()
