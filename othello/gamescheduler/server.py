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
import functools
import queue
import logging
import json
import traceback
import datetime

from .worker import GameRunner
from .utils import generate_id
from .settings import OTHELLO_AI_UNKNOWN_PLAYER, OTHELLO_GAME_MAX_TIME, \
        OTHELLO_GAME_MAX_TIMEDELTA 
from .cron_scheduler import CronScheduler

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

        self.started_when = datetime.datetime.utcnow()


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

        self.cron_scheduler = CronScheduler(self.loop)
        self.cron_scheduler.schedule_periodic(
                func=self.cleanup_all_games, args=[], kwargs=dict(),
                time=OTHELLO_GAME_MAX_TIME // 2, taskid='cleanup_all_games_task')
        self.cron_scheduler.start_task('cleanup_all_games_task')
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
        log.debug("{} assigning room id".format(new_id))
        transport.write((new_id+'\n').encode('utf-8'))
        self.check_room_validity(new_id)

    def gamerunner_emit_callback(self, event):
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
        self.check_room_validity(room_id)
        if type(data) is str:
            data = data.encode('utf-8')
        log.debug("{} will receive data {}".format(room_id, data))

        # Add newline to seperate out data in case multiple methods become
        # buffered into one message
        data = data + b'\n'

        if room_id not in self.rooms:
            # changing to debug b/c this happens so often
            log.debug("{} does not exist anymore! ignoring b/c probably already killed".format(room_id))
            return

        # don't send to a client that's disconnected
        if self.rooms[room_id].transport:
            if self.rooms[room_id].transport.is_closing():
                self.game_end_actual(room_id)
                # Early return because this closes all the watching ones anyway
                return
            else:
                log.debug("{} writing to transport".format(room_id))
                self.rooms[room_id].transport.write(data)

        for watching_id in self.rooms[room_id].watching:
            # same here, don't send to disconnected ppl
            if watching_id in self.rooms and self.rooms[watching_id].transport:
                if self.rooms[watching_id].transport.is_closing():
                    self.game_end_actual(watching_id)
                else:
                    log.debug("{} writing to watching transport".format(room_id))
                    self.rooms[watching_id].transport.write(data)

        self.rooms[room_id].watching = [w_id for w_id in self.rooms[room_id].watching if w_id in self.rooms]

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
            elif msg_type == 'disconnect':
                self.game_end(parsed_data, room_id)

    def eof_received(self):
        log.debug("Received EOF")

    # From client to server

    def list_games(self, parsed_data, room_id):
        self.check_room_validity(room_id)
        room_list = dict(
            (id, [self.rooms[id].black_ai, self.rooms[id].white_ai, self.rooms[id].timelimit]) \
            for id in self.rooms.keys() \
            if self.rooms[id].game
        )
        list_json = json.dumps(room_list) + '\n'
        self._send(list_json, room_id)

    def play_game(self, parsed_data, room_id):
        self.check_room_validity(room_id)
        
        black_ai = parsed_data.get('black', None)
        white_ai = parsed_data.get('white', None)
        timelimit = parsed_data.get('t', None)
        if black_ai is None or \
          white_ai is None or \
          timelimit is None:
            log.info("{} Play request was invalid! ignoring...".format(room_id))
            return

        log.info("{} Playing game: {} v {}".format(room_id, black_ai, white_ai))
        self.play_game_actual(black_ai, white_ai, timelimit, room_id)

    def play_game_actual(self, black_ai, white_ai, timelimit, room_id):
        game = GameRunner(black_ai, white_ai, timelimit, \
            self.loop, room_id, self.gamerunner_emit_callback)
        q = queue.Queue()
        executor = ThreadPoolExecutor()

        self.rooms[room_id].black_ai = black_ai
        self.rooms[room_id].white_ai = white_ai
        self.rooms[room_id].timelimit = timelimit
        self.rooms[room_id].game = game
        self.rooms[room_id].queue = q
        self.rooms[room_id].executor = executor
        self.rooms[room_id].started_when = datetime.datetime.utcnow()
        # here's where the **magic** happens. Tasks should be scheduled to run automatically
        log.debug("{} Starting game {} v {} ({})".format(
            room_id, black_ai, white_ai, timelimit
        ))
        self.rooms[room_id].task = self.loop.run_in_executor(executor, game.run, q)
        self.rooms[room_id].task.add_done_callback(
                lambda fut: self.game_end(dict(), room_id)
        )
        
        self.check_room_validity(room_id)

    def watch_game(self, parsed_data, room_id):
        self.check_room_validity(room_id)
        log.debug("{} watch_game".format(room_id))
        id_to_watch = parsed_data.get('watching', None)
        if id_to_watch is None:
            log.info("{} Watch request was invalid! ignoring...".format(room_id))
            return
        if id_to_watch not in self.rooms:
            log.warn("{} wants to watch game {}, but it doesn't exist!".format(room_id, id_to_watch))
            return

        self.rooms[id_to_watch].watching.append(room_id)

    def move_reply(self, parsed_data, room_id):
        self.check_room_validity(room_id)
        if self.rooms[room_id].queue:
            move = parsed_data.get('move', -1)
            log.debug("{} move_reply {}".format(room_id, move))
            self.rooms[room_id].queue.put_nowait(move)
        else:
            # don't have a queue to put in to
            log.warn("{} has no queue to put move {} into!".format(room_id, parsed_data))

    # From GameRunner to server

    def board_update(self, event, room_id):
        self.check_room_validity(room_id)
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
        self.check_room_validity(room_id)
        """
        Called when the game wants the user to input a move.
        Sends out a similar call to the client
        """
        log.debug("{} move_request {}".format(room_id, event))
        self._send_json({'type':"moverequest"}, room_id)

    def game_error(self, event, room_id):
        self.check_room_validity(room_id)
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
        if room_id not in self.rooms:
            log.debug("{} getting ended twice".format(room_id))
            return
        self.check_room_validity(room_id)
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
   
    # General utility methods

    def game_end_actual(self, room_id):
        log.debug("{} attempting to end".format(room_id))
        if room_id not in self.rooms: return
        log.debug("{} actually ending".format(room_id))

        if self.rooms[room_id].game:
            log.debug("{} setting do_quit to True".format(room_id))
            with self.rooms[room_id].game.do_quit_lock:
                self.rooms[room_id].game.do_quit = True
            log.debug("{} cancelling task".format(room_id))
            self.rooms[room_id].task.cancel()
            log.debug("{} shutting down executor".format(room_id))
            self.rooms[room_id].executor.shutdown(wait=True)

        log.debug("{} shutting down transport?".format(room_id))
        if self.rooms[room_id].transport:
            log.debug("{} yes, shutting down transport".format(room_id))
            self.rooms[room_id].transport.close()
        # avoiding any cylcical bs
        watching = self.rooms[room_id].watching.copy()
        del self.rooms[room_id]
        for watching_id in watching:
            self.game_end_actual(watching_id)

    def check_room_validity(self, room_id):
        try:
            if room_id not in self.rooms:
                log.debug("{} wasn't in self.rooms!".format(room_id))
                return False
            # Basic typing checks
            room = self.rooms[room_id]
            assert(room.id == room_id)
            assert(room.black_ai is None or isinstance(room.black_ai, str))
            assert(room.white_ai is None or isinstance(room.white_ai, str))
            assert(isinstance(room.timelimit, float) or isinstance(room.timelimit, int))
            assert(isinstance(room.watching, list))
            #for w_id in room.watching:
            #    assert(w_id in self.rooms)
            assert(room.transport is None or isinstance(room.transport, asyncio.BaseTransport))
            assert(room.game is None or isinstance(room.game, GameRunner))
            assert(room.queue is None or isinstance(room.queue, queue.Queue))
            assert(room.executor is None or isinstance(room.executor, ThreadPoolExecutor))
            assert(room.task is None or isinstance(room.task, asyncio.Future))
            assert(isinstance(room.started_when, datetime.datetime))

            # Extra checks if game is created:
            if not (room.game is None):
                # Make sure everything is defined
                assert(not (room.black_ai is None))
                assert(not (room.white_ai is None))
                assert(not (room.queue is None))
                assert(not (room.executor is None))
                assert(not (room.task is None))

                # Checks to make sure things are shutting down correctly
                with room.game.do_quit_lock:
                    if room.game.do_quit:
                        assert(room.task.done())
                        assert(room.transport is None or room.transport.is_closing())
                    
                    if room.task.done():
                        assert(room.game.do_quit)
                        assert(room.transport is None or room.transport.is_closing())

                    if not (room.transport is None) and room.transport.is_closing():
                        assert(room.game.do_quit)
                        assert(room.task.done())

            return True
        except AssertionError:
            log.warn(traceback.format_exc())
            return False

    # Needs to be async for... reasons
    # actually there is no reason I just would rather change this than
    # change the code that calls it
    async def cleanup_all_games(self):
        # to avoid repeated calls, why not
        current_time = datetime.datetime.utcnow()
        # can't change size of dictionary while iterating, create new dict instead
        # yeah storing everything in an in-memory dict isn't the best solution,
        # but DB stuff is worse I guarantee it
        rooms_to_remove = []
        for room_id in self.rooms.keys():
            room = self.rooms[room_id]

            if current_time > room.started_when + OTHELLO_GAME_MAX_TIMEDELTA:
                log.error("{} timed out! please figure out why.".format(room_id))
                rooms_to_remove.append(room_id)

        for room_id in rooms_to_remove:
            self.game_end_actual(room_id)
