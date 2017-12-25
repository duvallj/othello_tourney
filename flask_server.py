#!/usr/bin/python3

import socketio
import eventlet
import os
import socket
from flask import Flask
import argparse

from socketio_server import *
from run_ai_remote import LocalAIServer

eventlet.monkey_patch()

parser = argparse.ArgumentParser(description='Run the othello server, either on the vm part or the web part.')
parser.add_argument('--port', type=int, default=10770,
                    help='Port to listen on')
parser.add_argument('--hostname', type=str, default='127.0.0.1',
                    help='Hostname to listen on')
parser.add_argument('--remotes', type=str, nargs='*',
                    help='List of remote hosts to forward to')
parser.add_argument('--serve_ai_only', action='store_true',
                    help='If no remotes provided, tells whether or not this should include the web interface as well.')


args = parser.parse_args()
app = Flask(__name__)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<string:path>')
def serve(path):
    return app.send_static_file(path)

@app.route('/js/<string:file>')
def serve_js(file):
    return app.send_static_file('js/'+file)

@app.route('/images/<string:file>')
def serve_img(file):
    return app.send_static_file('images/'+file)

if __name__=='__main__':
    addr = socket.getaddrinfo(args.hostname, args.port)
    host, family = addr[0][4], addr[0][0]
    print('Listening on {} {}'.format(host, family))
    
    if args.remotes:
        args.remotes = list(map(lambda x:tuple(x.split("=")), args.remotes))
        #gm = GameForwarder(args.remotes)
        gm = GameManager(remotes=args.remotes)
    else:
        gm = GameManager(remotes=None)

    if args.serve_ai_only:
        srv = LocalAIServer(gm.possible_names)
        srv.run(host, family)
    else:
        srv = socketio.Middleware(gm, app)
        eventlet.wsgi.server(eventlet.listen(host, family), srv)
