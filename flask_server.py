#!/usr/bin/python3

import socketio
import eventlet
import os
import sys
import socket
import flask

eventlet.monkey_patch()

from flask_social import Social, SQLAlchemyConnectionDatastore
from flask_sqlalchemy import SQLAlchemy
from flask_security import SQLAlchemyUserDatastore, UserMixin, \
     RoleMixin, Security, login_required
import argparse

from socketio_server import *
from run_ai_remote import LocalAIServer
import ion_secret



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

app.config['SOCIAL_ION'] = {
    'id': 'ion',
    'module': 'ion_provider',
    'consumer_key': ion_secret.ION_OAUTH_KEY,
    'consumer_secret': ion_secret.ION_OAUTH_SECRET
}

db = SQLAlchemy(app)

roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    provider_id = db.Column(db.String(255))
    provider_user_id = db.Column(db.String(255))
    access_token = db.Column(db.String(255))
    secret = db.Column(db.String(255))
    display_name = db.Column(db.String(255))
    profile_url = db.Column(db.String(512))
    image_url = db.Column(db.String(512))
    rank = db.Column(db.Integer)

security = Security(app, SQLAlchemyUserDatastore(db, User, Role))
social = Social(app, SQLAlchemyConnectionDatastore(db, Connection))

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
    return flask.render_template('login.html')

@app.route('/upload')
@login_required
def upload():
    return flask.render_template('upload.html')

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
