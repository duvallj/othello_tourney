#!/usr/bin/python3

import socket
import os
import time
import argparse
import multiprocessing
from functools import wraps, update_wrapper
from datetime import datetime
import logging as log

import socketio
import flask
from flask import request
from flask_security import current_user

from socketio_server import GameManager
from othello_admin import Strategy
import Othello_Core as oc

core = Strategy()

parser = argparse.ArgumentParser(description='Run the othello server in tournament mode. Too much is different for it to be it the main_server.py file')
parser.add_argument('--port', type=int, default=10770,
                    help='Port to listen on')
parser.add_argument('--hostname', type=str, default='127.0.0.1',
                    help='Hostname to listen on')
parser.add_argument('--remotes', type=str, nargs='*',
                    help='List of remote hosts to forward to')
parser.add_argument('--base_folder', type=str, default=os.getcwd(),
                    help='Base folder to serve out of. (DONT USE)')
parser.add_argument('--jail_begin', type=str, default='',
                    help='Command to jail local AIs. "{NAME}" replaced with the name of the AI when run. If not specified, AIs are not jailed.')
parser.add_argument('--game_list', type=str,
                    help="File of list of names in \"name,name\\n\" format to run.")
parser.add_argument('--game_output', type=str,
                    help="Dir to log the tournament results to")
parser.add_argument('--game_delay', type=int, default=10,
                    help="Number of seconds the ais are allowed, AND the number of minutes each game will run")

app = flask.Flask(__name__)
app.gm = None
app.args = None

app.config['DEBUG'] = True

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/index')
def index2():
    return flask.render_template('index.html')

@app.route('/about')
def about():
    return flask.render_template('about_tournament.html')
    
"""
@app.route('/about_uploading')
def about_uploading():
    return flask.render_template('about_uploading.html')
"""
@app.route('/play')
def play():
    return flask.render_template('play_disabled.html')

@app.route('/upload')
def upload():
    return flask.render_template('upload_disabled.html')
    
@app.route('/watch')
def watch():
    return flask.render_template('watch.html')

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = flask.make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
        
    return update_wrapper(no_cache, view)
    
@app.route('/schedule')
@nocache
def schedule():
    file = open(args.game_list, 'r')
    data = file.read()
    file.close()
    return flask.render_template("schedule.html", schedule=data.split("\n"))
    
@app.route('/list/ais')
@nocache
def ailist():
    pn = sorted(app.gm.possible_names)
    log.debug(pn)
    return "\n".join(pn)
    
@app.route('/list/games')
@nocache
def gamelist():
    log.debug(app.gm.cdata.items())
    return "\n".join(','.join(map(str,(sid, cdata.game.BLACK_NAME, cdata.game.WHITE_NAME, cdata.game.timelimit))) for sid, cdata in app.gm.cdata.items() if cdata.game.playing)


def modified_act_on_message(sid, packet):
    mtype, data = packet
    log.debug("{} got packet ({}, {})".format(sid, mtype, data))
    if mtype == 'board':
        p1 = data.get('black', 'Unknown')
        p2 = data.get('white', 'Unknown')
        board = data.get('board', oc.EMPTY*64)
        logfile = open(os.path.join(app.args.game_output, "{0}_{1}.txt".format(p1, p2)), 'a')
        logfile.write("{}{}-{}\n\n".format(
            core.print_board(board), 
            board.count(oc.BLACK),
            board.count(oc.WHITE)
        ))
        app.gm.emit('reply', data=data, room=sid)
    elif mtype == 'getmove':
        app.gm.emit('moverequest', data=dict(), room=sid)
    elif mtype == 'gameend':
        black_score = data.get('black_score', 0)
        black = data.get('black', 'Unknown')
        white = data.get('white', 'Unknown')
        err_msg = data.get('err_msg', "No error") or "No error"
        outfile = open(os.path.join(app.args.game_output, 'results.txt'), 'a')
        outfile.write("{},{},{},{}\n".format(black, white, black_score, repr(err_msg)))
        outfile.close()
        outfile = open(os.path.join(app.args.game_output, "{0}_{1}.txt"), 'a')
        outfile.write("winner:{},{}".format(
            [
                black + " and " + white + " tied",
                black + " won",
                white + " won"
            ][int(black_score/abs(black_score))],
            repr(err_msg)
        ))
        log.debug("Did log results of {} to file".format(sid))
        app.gm.emit('gameend', data=data, room=sid)
    
def run_all_games(gm, args):
    time.sleep(5)
    log.debug("Starting games")
    file = open(args.game_list, 'r')
    data = file.read()
    file.close()
    file = open(os.path.join(args.game_output, "results.txt"), 'w')
    file.write("Black,White,Score,Error\n")
    file.close()
    sid1 = '0'
    sid2 = '1'
    for line in data.split("\n"):
        line = line.strip()
        if line:
            ai1, ai2 = line.split(',')
            log.info("Now playing {} vs {}".format(ai1, ai2))
            gm.create_game(sid1, None)
            gm.create_game(sid2, None)
            lf1 = open(os.path.join(args.game_output, "{0}_{1}.txt".format(ai1, ai2)), 'w')
            lf1.write("{0},{1}\n".format(ai1, ai2))
            lf2 = open(os.path.join(args.game_output, "{1}_{0}.txt".format(ai1, ai2)), 'w')
            lf2.write("{1},{0}\n".format(ai1, ai2))
            lf1.close()
            lf2.close()
            log.debug("Games were created")
            gm.start_game(sid1, {'black': ai1, 'white': ai2, 'tml': args.game_delay})
            gm.start_game(sid2, {'black': ai2, 'white': ai1, 'tml': args.game_delay})
            log.debug("Successfully started games")
            while gm.cdata[sid1].proc.is_alive() or gm.cdata[sid2].proc.is_alive():
                time.sleep(args.game_delay)
            gm.cdata[sid1].proc.join()
            gm.cdata[sid2].proc.join()
            log.debug("Games ended")
            gm.delete_game(sid1)
            gm.delete_game(sid2)
            log.debug("Game data deleted")
            sid1 = str(int(sid1)+2)
            sid2 = str(int(sid2)+2)
    file.close()
    log.info("All games run")

if __name__ == "__main__":
    import eventlet
    eventlet.monkey_patch()
    log.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=log.DEBUG)

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
    
    setattr(gm, 'act_on_message', modified_act_on_message)
    
    app.args = args
    app.gm = gm
    srv = socketio.Middleware(gm, app)
    proc = eventlet.spawn(run_all_games, gm, args)
    eventlet.wsgi.server(eventlet.listen(host, family), srv)
