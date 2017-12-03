#!/usr/bin/python3

from better_sio import *
import socketio
import eventlet
import os
from flask import Flask

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
    os.environ['PORT']='10770'
    print('Listening on port '+str(os.environ['PORT']))
    gm = GameManager()
    gm.write_ai()

    srv = socketio.Middleware(gm, app)
    eventlet.wsgi.server(eventlet.listen(('localhost', int(os.environ['PORT']))), srv)
