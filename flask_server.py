#!/usr/bin/python3

import socketio
import eventlet
import os
from flask import Flask
import argparse

from socketio_server import *

eventlet.monkey_patch()

parser = argparse.ArgumentParser(description='Run the othello server, either on the vm part or the web part.')
parser.add_argument('--port', type=int, default=10770,
                    help='Port to listen on')
parser.add_argument('--remotes', type=str, nargs='*',
                    help='List of remote hosts to forward to')
parser.add_argument('--local', help='Listen only on localhost?')

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
    print('Listening on port '+str(args.port))
    if args.remotes:
        gm = GameForwarder(list(map(lambda x:tuple(x.split(":")), args.remotes)))
    else:
        gm = GameManager()
    gm.write_ai()

    srv = socketio.Middleware(gm, app)
    target = 'localhost' if args.local else ''
    eventlet.wsgi.server(eventlet.listen((target, args.port)), srv)
