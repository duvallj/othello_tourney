import os
import socket_server_oth as sso
#import socket_client_oth as sco
import improved_runner as iro
import multiprocessing as mp
import importlib

import socketio
import eventlet

import sys

ailist_filename = 'C:/Users/Me/Documents/GitHub/othello_tourney/www/ai_port_info.txt'
name2strat = dict()
sio = socketio.Server()

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
    pfile = open(ailist_filename, 'w')
    pfile.write(buf[:-1])
    pfile.close()

sid2queue = dict()
sid2lsrcv = dict()
sid2game = dict()

@sio.on('connect')
def connect(sid, environ):
    print('connect',sid)
    sio.enter_room(sid, "room_"+sid)
    sys.stdout.flush()

@sio.on('0prequest')
def make_reg_game(sid, data):
    print(data)
    parent_conn, child_conn = mp.Pipe()
    sid2queue[sid] = parent_conn
    sid2lsrcv[sid] = {'bSize':'8',
                      'board':'...........................o@......@o...........................',
                      'black':data['black'], 'white':data['white']}

    game = mp.Process(target=iro.play_game, args=(data['black'],
                                                  data['white'],
                                                  child_conn,
                                                  name2strat))
    game.start()
    sid2game[sid] = game

# 1prequest

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
    print('disconnected',sid)
    sio.leave_room(sid, "room_"+sid)
    sys.stdout.flush()

if __name__=="__main__":
    spin_up_threads()
    app = socketio.Middleware(sio)
    eventlet.wsgi.server(eventlet.listen(('', 7531)), app)
    
