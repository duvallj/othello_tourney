"""
##########################
#         WARNING        #
##########################

You should not read this or `othello.apps.games.consumers` without first looking at
the file `run_ai_layout.txt' at the root of this repo. It contains the basic
layout for how everything fits together to run a game, which is really hard to
understand otherwise.

Debuggig any of this is not for the faint of heart. Consider yourself warned.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import queue
import logging
import json

from .worker import GameRunner
from .utils import generate_id
from .settings import OTHELLO_AI_UNKNOWN_PLAYER
from .othello_core import BLACK, WHITE, EMPTY

log = logging.getLogger(__name__)

class Room:
    """
    Utility class that stores information about a game room
    """
    def __init__(self):
        self.id = None
        self.black_ai = None
        self.white_ai = None
        self.timelimit = 5.0
        self.watching = []

        self.transport = None
        self.game = None
        self.queue = None
        self.task = None
        self.executor = None


class GameScheduler(asyncio.Protocol):
    """
    Now hold on a hot minute isn't this just a Consumer but asyncio???
    Thing is, you can pass *the same* protocol object to asyncio's
    create_connection, which allows it to store a bunch of state
    unlike in Django Channels, where a new Consumer is created for
    every client.

    THE ONLY REASON I HAVE TO FORWARD REQUESTS TO THIS SERVER THROUGH
    CHANNELS IS THAT ASYNCIO DOESN'T SUPPORT WEBSOCKETS GOSH DARN IT.
    """
    def __init__(self, loop):
        super().__init__()
        self.loop = loop
        self.rooms = dict()
        log.debug("Made GameScheduler")

    def connection_made(self, transport):
        log.debug("Received connection")
        new_id = generate_id()
        # extremely low chance to block, ~~we take those~~
        while new_id in self.rooms: new_id = generate_id()
        room = Room()
        room.id = new_id
        room.transport = transport
        self.rooms[new_id] = room
        log.debug("Assigning room id {}".format(new_id))
        transport.write((new_id+'\n').encode('utf-8'))

    def gamerunner_callback(self, event):
        log.debug("Got data from subprocess: {}".format(event))
        msg_type = event.get('type', None)
        room_id = event.get('room_id', None)
        if not msg_type or not room_id:
            log.warn("Data from subprocess was invalid! ack!")
            return

        if msg_type == 'board.update':
            self.board_update(event, room_id)
        elif msg_type == 'move.request':
            self.move_request(event, room_id)
        elif msg_type == 'game.end':
            self.game_end(event, room_id)
        elif msg_type == 'game.error':
            self.game_error(event, room_id)

    def connection_lost(self, exc):
        log.debug("Lost connection")

    def _send(self, data, room_id):
        if type(data) is str:
            data = data.encode('utf-8')
        log.debug("sending out {} to {}".format(data, room_id))

        # Add newline to seperate out data in case multiple methods become
        # buffered into one message
        data = data + b'\n'

        if room_id not in self.rooms:
            # changing to debug b/c this happens so often
            log.debug("room_id {} does not exist anymore! ignoring b/c probably already killed".format(room_id))
            return

        # don't send to a client that's disconnected
        if self.rooms[room_id].transport:
            if self.rooms[room_id].transport.is_closing():
                self.game_end_actual(room_id)
                # Early return because this closes all the watching ones anyway
                return
            else:
                log.debug("Writing to transport {}".format(room_id))
                self.rooms[room_id].transport.write(data)

        for watching_id in self.rooms[room_id].watching:
            # same here, don't send to disconnected ppl
            if watching_id in self.rooms and self.rooms[watching_id].transport:
                if self.rooms[watching_id].transport.is_closing():
                    self.game_end_actual(watching_id)
                else:
                    log.debug("Writing to watching transport {}".format(room_id))
                    self.rooms[watching_id].transport.write(data)

    def _send_json(self, data, room_id):
        json_data = json.dumps(data)
        self._send(json_data, room_id)

    def data_received(self, data):
        log.debug("Received data {}".format(data))
        # taking HUGE assumption here that all data is properly line-buffered
        # should mostly work out tho, the packets are tiny
        parsed_data = None
        parsed_data = json.loads(data.decode('utf-8').strip())
        log.debug("Parsed data in {}".format(parsed_data))

        if not (parsed_data is None):
            room_id = parsed_data.get('room_id', None)
            if room_id is None or room_id not in self.rooms: return
            # yes, you read that code right, even simple utility calls
            # need to be identified w/ a room. Downside to a single class :/

            # I'm honestly not sure why I'm not just transparently passing data
            # through and going through all the trouble of sanitizing it here.
            # I control the GameRunner, supposedly, no need to worry? idk just leave it.
            msg_type = parsed_data.get('type', 'list_request')
            if msg_type == 'list_request':
                self.list_games(parsed_data, room_id)
            elif msg_type == 'play_request':
                self.play_game(parsed_data, room_id)
            elif msg_type == 'watch_request':
                self.watch_game(parsed_data, room_id)
            elif msg_type == 'movereply':
                self.move_reply(parsed_data, room_id)

    def eof_received(self):
        log.debug("Received EOF")

    # From client to server

    def list_games(self, parsed_data, room_id):
        room_list = dict(
            (id, [self.rooms[id].black_ai, self.rooms[id].white_ai, self.rooms[id].timelimit]) \
            for id in self.rooms.keys() \
            if self.rooms[id].game
        )
        list_json = json.dumps(room_list) + '\n'
        self._send(list_json, room_id)

    def play_game(self, parsed_data, room_id):
        black_ai = parsed_data.get('black', None)
        white_ai = parsed_data.get('white', None)
        timelimit = parsed_data.get('t', None)
        if black_ai is None or \
          white_ai is None or \
          timelimit is None:
            log.info("Play request was invalid! ignoring...")
            return

        self.play_game_actual(black_ai, white_ai, timelimit, room_id)

    def play_game_actual(self, black_ai, white_ai, timelimit, room_id):
        game = GameRunner(black_ai, white_ai, timelimit, \
            self.loop, room_id, self.gamerunner_callback)
        q = queue.Queue()
        executor = ThreadPoolExecutor()

        self.rooms[room_id].black_ai = black_ai
        self.rooms[room_id].white_ai = white_ai
        self.rooms[room_id].timelimit = timelimit
        self.rooms[room_id].game = game
        self.rooms[room_id].queue = q
        self.rooms[room_id].executor = executor
        # here's where the **magic** happens. Tasks should be scheduled to run automatically
        log.debug("Starting game {} v {} ({}) for room {}".format(
            black_ai, white_ai, timelimit, room_id
        ))
        self.rooms[room_id].task = self.loop.run_in_executor(executor, game.run, q)


    def watch_game(self, parsed_data, room_id):
        log.debug("watch_game from {}".format(room_id))
        id_to_watch = parsed_data.get('watching', None)
        if id_to_watch is None:
            log.info("Watch request was invalid! ignoring...")
            return
        if id_to_watch not in self.rooms:
            log.warn("Client wants to watch game {}, but it doesn't exist!".format(id_to_watch))
            return

        self.rooms[id_to_watch].watching.append(room_id)

    def move_reply(self, parsed_data, room_id):
        if self.rooms[room_id].queue:
            move = parsed_data.get('move', -1)
            log.debug("{} move_reply {}".format(room_id, move))
            self.rooms[room_id].queue.put_nowait(move)
        else:
            # don't have a queue to put in to
            log.warn("Room {} has no queue to put move {} into!".format(room_id, parsed_data))

    # From GameRunner to server

    def board_update(self, event, room_id):
        """
        Called when there is an update on the board
        that we need to send to the client
        """
        log.debug("{} board_update {}".format(room_id, event))
        self._send_json({
            'type': 'reply',
            'board': event.get('board', ""),
            'tomove': event.get('tomove', "?"),
            'black': event.get('black', OTHELLO_AI_UNKNOWN_PLAYER),
            'white': event.get('white', OTHELLO_AI_UNKNOWN_PLAYER),
            'bSize': '8',
        }, room_id)

    def move_request(self, event, room_id):
        """
        Called when the game wants the user to input a move.
        Sends out a similar call to the client
        """
        log.debug("{} move_request {}".format(room_id, event))
        self._send_json({'type':"moverequest"}, room_id)

    def game_error(self, event, room_id):
        """
        Called whenever the AIs/server errors out for whatever reason.
        Could be used in place of game_end
        """
        log.debug("{} game_error {}".format(room_id, event))
        self._send_json({
            'type': "gameerror",
            'error': event.get('error', "No error"),
        }, room_id)
        # game_end is called after this, no need to ternimate room just yet

    def game_end(self, event, room_id):
        """
        Called when the game has ended, tells client that message too.
        Really should log the result but doesn't yet.
        """
        log.debug("{} game_end {}".format(room_id, event))
        self._send_json({
            'type': "gameend",
            'winner': event.get('winner', "?"),
            'forfeit': event.get('forfeit', False),
            'board': event.get('board', ""),
        }, room_id)
        self.game_end_actual(room_id)

    def game_end_actual(self, room_id):
        log.debug("attempting to end {}".format(room_id))
        if room_id not in self.rooms: return
        log.debug("actually ending {}".format(room_id))

        if self.rooms[room_id].game:
            with self.rooms[room_id].game.do_quit_lock:
                self.rooms[room_id].game.do_quit = True
            self.rooms[room_id].task.cancel()
            self.rooms[room_id].executor.shutdown(wait=True)
            #self.rooms[room_id].game.cleanup() # shouldn't be necessary, already gets called

        if self.rooms[room_id].transport:
            self.rooms[room_id].transport.close()
        # avoiding any cylcical bs
        watching = self.rooms[room_id].watching.copy()
        del self.rooms[room_id]
        for watching_id in watching:
            self.game_end_actual(watching_id)


class TournamentScheduler(GameScheduler):
    """
    A subclass that doesn't allow anyone to make new games, and
    is instead started with a list of initial games to start running.
    Logs results of tournament to CSV file for easy processing,
    either by Django shell or other method.
    """

    """
    Available tournament types:
    'rr': Round robin, everybody plays everybody else at least once.
    (not implemented) 'bracket': Bracket auto-seeded based on ranking provided
        in input list (towards front = higher rank).
    """

    def __init__(self, loop, completed_callback, ai_list, timelimit, tournament_type='rr', tournament_args=dict()):
        super().__init__(loop)

        self.completed_callback = completed_callback
        self.ai_list = ai_list
        self.timelimit = timelimit
        self.tournament_type = tournament_type
        self.tournament_args = tournament_args

        self.game_queue = queue.Queue()
        self.results = []
        self.results_lock = Lock()

        # populate queue with initial matchups to play
        if self.tournament_type == 'rr':
            import itertools
            for black, white in itertools.permutations(self.ai_list, 2):
                self.game_queue.put_nowait((black, white))

        # independent of tournament type, start running as many games as we can
        for x in range(self.tournament_args.get('num_games', 2)):
            if not self.game_queue.empty():
                self.loop.call_soon_threadsafe(self.play_tournament_game, *self.game_queue.get_nowait())

    def play_game(self, parsed_data, room_id):
        # send an error message back telling them they can't play
        log.warn("Client {} tried to play during a tournament".format(room_id))
        self.game_error({'error': "You cannot start a game during a tournament."}, room_id)
        self.game_end(dict(), room_id)

    def play_tournament_game(self, black, white):
        log.info("Playing next game: {} v {}".format(black, white))
        new_id = generate_id()
        # extremely low chance to block, ~~we take those~~
        while new_id in self.rooms: new_id = generate_id()
        room = Room()
        room.id = new_id
        self.rooms[new_id] = room
        log.debug("Creating new room id {}".format(new_id))

        self.play_game_actual(black, white, self.timelimit, new_id)

    def game_end(self, parsed_data, room_id):
        log.debug("Overridded game_end called")
        # log result
        board = parsed_data.get('board', "")
        forfeit = parsed_data.get('forfeit', False)
        winner = parsed_data.get('winner', '?')
        black_score = board.count(BLACK)
        white_score = board.count(WHITE)
        black_ai = self.rooms[room_id].black_ai
        white_ai = self.rooms[room_id].white_ai

        with self.results_lock:
            result = (
                black_ai, white_ai, black_score, white_score, winner, int(forfeit),
            )

            self.results.append(result)

        log.debug("Added to results: {}".format(result))

        super().game_end(parsed_data, room_id)

        # handle putting new games into queue, if necessary
        if self.tournament_type == 'rr':
            if not self.game_queue.empty():
                self.loop.call_soon_threadsafe(self.play_tournament_game, *self.game_queue.get_nowait())
            else:
                log.info("Tournament completed! Returning results...")
                self.loop.call_soon_threadsafe(self.completed_callback, self.results, self.results_lock)
