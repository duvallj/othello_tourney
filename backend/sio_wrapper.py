import os
import time
import ctypes
import sys

import multiprocessing as mp
import socketio
import eventlet
import importlib

from othello_admin import *


ailist_filename = 'C:/Users/Me/Documents/GitHub/othello_tourney/www/ai_port_info.txt'
name2strat = dict()
eventlet.monkey_patch() # why is this name
mgr = socketio.KombuManager('redis://')
sio = socketio.Server(client_manager=mgr)

def get_possible_files():
    folders = os.listdir(os.getcwd()+'/Students')
    return ['Students.'+x+'.strategy' for x in folders if x != '__pycache__']

def spin_up_threads():
    files = get_possible_files()
    buf = ''
    old_path = os.getcwd()
    old_sys = sys.path
    for x in range(len(files)):
        name = files[x].split('.')[1]
        path = old_path+'/Students/'+name
        os.chdir(path)
        sys.path = [path] + old_sys
        name2strat[name] = importlib.import_module(files[x]).Strategy().best_strategy
        buf += name +'\n'
    name2strat['you'] = None
    pfile = open(ailist_filename, 'w')
    pfile.write(buf[:-1])
    pfile.close()

sid2queue = dict()
sid2lsrcv = dict()
sid2game = dict()
sid2mrq = dict()

@sio.on('connect')
def connect(sid, environ):
    print('connect',sid)
    sio.enter_room(sid, "room_"+sid)
    sys.stdout.flush()

@sio.on('prequest')
def make_reg_game(sid, data):
    print(data)
    parent_conn, child_conn = mp.Pipe()
    sid2queue[sid] = parent_conn
    sid2lsrcv[sid] = {'bSize':'8',
                      'board':'...........................o@......@o...........................',
                      'black':data['black'], 'white':data['white']}

    game = mp.Process(target=play_game, args=(data['black'],
                                            data['white'],
                                            child_conn,
                                            name2strat,
                                            sid))
    game.start()
    sid2game[sid] = game
    sid2mrq[sid] = False

@sio.on('refresh')
def send_reply(sid, data):
    print('refreshing ',sid)
    while sid2queue[sid].poll():
        sid2lsrcv[sid] = sid2queue[sid].recv()
    sio.emit('reply',data=sid2lsrcv[sid],room=sid)
    sys.stdout.flush()

@sio.on('disconnect')
def disconnect(sid):
    del sid2queue[sid]
    del sid2lsrcv[sid]
    del sid2game[sid]
    del sid2mrq[sid]
    print('disconnected',sid)
    sio.leave_room(sid, "room_"+sid)
    sys.stdout.flush()

TIMELIMIT = 5

def get_move(strategy, board, player, time_limit):
    best_shared = mp.Value("i", -1)
    best_shared.value = 11
    running = mp.Value("i", 1)
    p = mp.Process(target=strategy, args=(board, player, best_shared, running))
    p.start()
    t1 = time.time()
    p.join(time_limit)
    running.value = 0
    time.sleep(0.01)
    p.terminate()
    time.sleep(0.01)
    handle = ctypes.windll.kernel32.OpenProcess(1, False, p.pid)
    ctypes.windll.kernel32.TerminateProcess(handle, -1)
    ctypes.windll.kernel32.CloseHandle(handle)
    #if p.is_alive(): os.kill(p.pid, signal.SIGKILL)
    move = best_shared.value
    return move

def get_player_move(sid, board, player):
    p_end, c_end = mp.Pipe()
    sid2mrq[sid] = (board, player, c_end)
    sio.emit('moverequest',room=sid)
    print('move request sent')
    return p_end.recv()

@sio.on('movereply')
def recv_player_move(sid, data):
    if sid2mrq[sid]:
        move = int(data['move'])
        print('recv move '+str(move))
        sys.stdout.flush()
        board, player, conn = sid2mrq[sid]
        if admin.is_legal(move, player, board):
            conn.send(move)
            sid2mrq[sid] = False
        else:
            sio.emit('moverequest',room=sid)
    

def play_game(nameA, nameB, conn, name2strat, sid):
    admin = Strategy()
    
    strategy = {core.BLACK:name2strat[nameA], core.WHITE:name2strat[nameB]}
    names ={core.BLACK:nameA, core.WHITE:nameB}

    player = core.BLACK
    board = admin.initial_board()

    forfeit = False

    while player is not None and not forfeit:
        if names[player] == 'you':
            move = get_player_move(sid, board, player)
        else:
            move = get_move(strategy[player], board, player, TIMELIMIT)
        if not admin.is_legal(move, player, board):
            forfeit = True
            if player == core.BLACK:
                black_score = -100
            else:
                black_score = 100
            continue
        board = admin.make_move(move, player, board)
        player = admin.next_player(board, player)
        black_score = admin.score(core.BLACK, board)

        conn.send({'bSize':'8',
                   'board':''.join(board).replace('?',''),
                   'black':nameA,
                   'white':nameB,
                   'tomove':player})

if __name__=="__main__":
    spin_up_threads()
    app = socketio.Middleware(sio)
    eventlet.wsgi.server(eventlet.listen(('', 7531)), app)
    
