import os
import socket_server_oth as sso
#import socket_client_oth as sco
import improved_runner as iro
import multiprocessing as mp

import socketio
import eventlet

import sys

portlist_filename = 'C:/Users/Me/Documents/GitHub/othello_tourney/www/ai_port_info.txt'
sio = socketio.Server()

def get_possible_files():
    folders = os.listdir(os.getcwd()+'/Students')
    return ['Students.'+x+'.strategy' for x in folders if x != '__pycache__']

def spin_up_threads():
    files = get_possible_files()
    buf = ''
    for x in range(len(files)):
        p = mp.Process(target=sso.Main, args=(files[x], 'localhost', x+5000))
        p.start()
        buf += files[x].split('.')[1]+':'+str(x+5000)+'\n'
    pfile = open(portlist_filename, 'w')
    pfile.write(buf[:-1])
    pfile.close()

sid2queue = dict()
sid2lsrcv = dict()
sid2game = dict()

@sio.on('connect')
def connect(sid, environ):
    print('connect',sid)
    sys.stdout.flush()

@sio.on('0prequest')
def make_reg_game(sid, data):
    print(data)
    blackport = int(data['black'])
    whiteport = int(data['white'])
    parent_conn, child_conn = mp.Pipe()
    sid2queue[sid] = parent_conn
    sid2lsrcv[sid] = {'bSize':'3', 'board':'ooo...@@@', 'black':'-1', 'white':'-1'}

    game = mp.Process(target=iro.play_game, args=(blackport, whiteport, child_conn))
    game.start()
    sid2game[sid] = game

# 1prequest

@sio.on('refresh')
def send_reply(sid, data):
    while sid2queue[sid].poll():
        sid2lsrcv[sid] = sid2queue[sid].recv()
    sio.emit('reply',data=sid2lsrcv[sid])

@sio.on('disconnect')
def disconnect(sid):
    del sid2queue[sid]
    del sid2lsrcv[sid]
    del sid2game[sid]
    print('disconnected',sid)
    sys.stdout.flush()

if __name__=="__main__":
    spin_up_threads()
    app = socketio.Middleware(sio)
    eventlet.wsgi.server(eventlet.listen(('', 7531)), app)
    
