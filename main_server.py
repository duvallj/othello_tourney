#!/usr/bin/python3

import socket
import os
import argparse
import multiprocessing

import socketio

from socketio_server import *
from run_ai_remote import LocalAIServer

parser = argparse.ArgumentParser(description='Run the othello server, either on the vm part or the web part.')
parser.add_argument('--port', type=int, default=10770,
                    help='Port to listen on')
parser.add_argument('--hostname', type=str, default='127.0.0.1',
                    help='Hostname to listen on')
parser.add_argument('--remotes', type=str, nargs='*',
                    help='List of remote hosts to forward to')
parser.add_argument('--serve_ai_only', action='store_true',
                    help='If no remotes provided, tells whether or not this should include the web interface as well.')
parser.add_argument('--base_folder', type=str, default=os.getcwd(),
                    help='Base folder to serve out of. (DONT USE)')
parser.add_argument('--jail_begin', type=str, default='',
                    help='Command to jail local AIs. "{NAME}" replaced with the name of the AI when run. If not specified, AIs are not jailed.')
                    
#args = parser.parse_args()

#gm = GameManager(".", async_mode='threading',
#jail_begin="C:/Python36/python.exe C:/Users/Me/Documents/Github/othello_tourney/run_ai_jailed_twisted.py")
#from flask_server import app
#app.gm = gm
#app.args = argparse.Namespace(base_folder=".")
#srv = socketio.Middleware(gm, app)

if __name__=='__main__':
    import eventlet
    eventlet.monkey_patch()

    args = parser.parse_args()
    multiprocessing.set_start_method('spawn')
    addr = socket.getaddrinfo(args.hostname, args.port)
    host, family = addr[0][4], addr[0][0]
    print('Listening on {} {}'.format(host, family))
    
    if args.remotes:
        args.remotes = list(map(lambda x:tuple(x.split("=")), args.remotes))
        gm = GameManager(args.base_folder, remotes=args.remotes, jail_begin=None)
    else:
        gm = GameManager(args.base_folder, remotes=None, jail_begin=args.jail_begin)

    if args.serve_ai_only:
        srv = LocalAIServer(gm.possible_names, args.base_folder, args.jail_begin)
        srv.run(host, family)
    else:
        from flask_server import app
        app.gm = gm
        app.args = args
        srv = socketio.Middleware(gm, app)
        eventlet.wsgi.server(eventlet.listen(host, family), srv)
        
    
