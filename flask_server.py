#!/usr/bin/python3

import socketio
import eventlet
import os
import socket
import flask
from flask_login import LoginManager, login_required
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
app = flask.Flask(__name__)

#Using flask-login
login_manager = LoginManager()
login_manager.init_app(app)

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/index')
def index2():
    return flask.render_template('index.html')

@app.route('/about')
def about():
    return flask.render_template('about.html')

@app.route('/play')
def play():
    return flask.render_template('othello.html')

@app.route('/login')
def login():
    # Use Ion Oauth stuff
    pass

@app.route('/upload')
@login_required
def upload():
    pass

@app.route('/logout')
@login_required
def logout():
    pass

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
