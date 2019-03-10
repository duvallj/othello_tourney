import asyncio
from concurrent.futures import ThreadPoolExecutor
import queue
import logging
import json

from .worker import GameRunner
from .utils import generate_id
from .settings import OTHELLO_AI_UNKNOWN_PLAYER
from .settings import LOGGING_HANDLERS, LOGGING_FORMATTER, LOGGING_LEVEL

log = logging.getLogger(__name__)
for handler in LOGGING_HANDLERS:
    log.addHandler(handler)
log.setLevel(LOGGING_LEVEL)

class Room:
    """
    Utility class that stores information about a game room
    """
    id = None
    black_ai = None
    white_ai = None
    timelimit = 5.0
    watching = []

    transport = None
    game = None
    queue = None
    task = None
    executor = None


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
        log.debug("Recieved connection")
        new_id = generate_id()
        # extremely low chance to block, ~~we take those~~
        while new_id in self.rooms: new_id = generate_id()
        room = Room()
        room.id = new_id
        room.transport = transport
        self.rooms[new_id] = room
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

        # don't send to a client that's disconnected
        if self.rooms[room_id].transport.is_closing():
            self._game_end_actual(room_id)
        else:
            self.rooms[room_id].transport.write(data)
            for watching_id in self.rooms[room_id].watching:
                if watching_id in self.rooms:
                    self.rooms[watching_id].transport.write(data)

    def _send_json(self, data, room_id):
        json_data = json.dumps(data)
        self._send(json_data, room_id)

    def data_received(self, data):
        log.debug("Recieved data {}".format(data))
        # taking HUGE assumption here that all data is properly line-buffered
        # should mostly work out tho, the packets are tiny
        parsed_data = None
        parsed_data = json.loads(data.decode('utf-8').strip())

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
            elif msg_type == 'move_reply':
                self.move_reply(parsed_data, room_id)

    def eof_received(self):
        log.debug("Recieved EOF")

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
            log.warn("Play request was invalid! ignoring...")
            return

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
        self.rooms[room_id].task = self.loop.create_task(self.loop.run_in_executor(executor, game.run, q))


    def watch_game(self, parsed_data, room_id):
        id_to_watch = parsed_data.get('watching', None)
        if id_to_watch is None:
            log.warn("Watch request was invalid! ignoring...")
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
            pass

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
        }, room_id)
        self._game_end_actual(room_id)

    def _game_end_actual(self, room_id):
        if room_id not in self.rooms: return

        if self.rooms[room_id].game:
            self.rooms[room_id].task.cancel()
            self.rooms[room_id].executor.shutdown(wait=False)
            # self.rooms[room_id].game.cleanup() # shouldn't be necessary, already gets called

        self.rooms[room_id].transport.close()
        # avoiding any cylcical bs
        watching = self.rooms[room_id].watching.copy()
        del self.rooms[room_id]
        for watching_id in watching:
            self._game_end_actual(watching_id)


class TournamentScheduler(GameScheduler):
    """
    A subclass that doesn't allow anyone to make new games, and
    is instead started with a list of initial games to start running.
    Logs results of tournament in aztr format.
    """
    pass
