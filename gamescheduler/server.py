import asyncio
from concurrent.futures import ThreadPoolExecutor
import queue
import logging
import json

from .worker import GameRunner
from .utils import generate_id
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

    transports = []
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
        log.info("Made GameScheduler")

    def connection_made(self, transport):
        log.info("Recieved connection")
        new_id = generate_id()
        # extremely low chance to block, ~~we take those~~
        while new_id in self.rooms: new_id = generate_id()
        room = Room()
        room.id = new_id
        room.transports.append(transport)
        self.rooms[new_id] = room
        transport.write((new_id+'\n').encode('utf-8'))

    def gamerunner_callback(self, data):
        log.info("Got data from subprocess: {}".format(data))

    def connection_lost(self, exc):
        log.info("Lost connection")

    def _send(self, data, room_id):
        if type(data) is str:
            data = data.encode('utf-8')
        for transport in self.rooms[room_id].transports:
            transport.write(data)

    def data_received(self, data):
        log.info("Recieved data {}".format(data))
        # taking HUGE assumption here that all data is properly line-buffered
        # should mostly work out tho, the packets are tiny
        parsed_data = None
        parsed_data = json.loads(data.decode('utf-8').strip())

        if not (parsed_data is None):
            room_id = parsed_data.get('room_id', None)
            if room_id is None: return
            # yes, you read that code right, even simple utility calls
            # need to be identified w/ a room. Downside to a single class :/

            msg_type = parsed_data.get('type', 'list_request')
            if msg_type == 'list_request':
                self.list_games(parsed_data, room_id)
            elif msg_type == 'play_request':
                self.start_game(parsed_data, room_id)
            elif msg_type == 'watch_request':
                self.watch_game(parsed_data, room_id)
            elif msg_type == 'move_reply':
                self.handle_move(parsed_data, room_id)

    def eof_received(self):
        log.info("Recieved EOF")

    def list_games(self, parsed_data, room_id):
        room_list = dict(
            (id, [self.rooms[id].black_ai, self.rooms[id].white_ai, self.rooms[id].timelimit]) \
            for id in self.rooms.keys() \
            if self.rooms[id].game
        )
        list_json = json.dumps(room_list) + '\n'
        self._send(list_json, room_id)

    def start_game(self, parsed_data, room_id):
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
        pass

    def handle_move(self, parsed_data, room_id):
        pass

class TournamentScheduler(GameScheduler):
    """
    A subclass that doesn't allow anyone to make new games, and
    is instead started with a list of initial games to start running.
    Logs results of tournament in aztr format.
    """
    pass
