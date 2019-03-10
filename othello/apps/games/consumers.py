"""
##########################
#         WARNING        #
##########################

Attempting to understand this file easily has the potential to make anyone go
insane. It did me in, that's for sure, and I wrote it.

You should probably check out `run_ai_layout.txt' at the root of this repo
before reading any further, it has the basic layout for how everything in this
app fits together to run a game.

Debuggig this is not for the faint of heart. Consider yourself warned.
"""

from django.conf import settings
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import sync_to_async, async_to_sync
from channels.exceptions import StopConsumer
import asyncio
from concurrent.futures import ThreadPoolExecutor

import logging
import json

from ...gamescheduler.client import game_scheduler_client_factory
from ...gamescheduler.utils import safe_int

log = logging.getLogger(__name__)

class GameConsumer(JsonWebsocketConsumer):
    """
    The consumer the handle websocket connections with game clients.

    Does no actual game running itself, just provides an interface to the tasks that do.

    Just for reference, it seems a new one of these is created for each new client.
    """

    # #### Websocket event handlers

    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        self.loop = asyncio.get_event_loop()
        self.room_fut = self.loop.create_future()
        self.transport, self.protocol = async_to_sync(self.loop.create_connection(
            game_scheduler_client_factory(self.loop, self.first_init, self.handle_outgoing),
            host=settings.SCHEDULER_HOST,
            port=settings.SCHEDULER_PORT
        ))
        self.room_id = None

    def first_init(self, data):
        # called when we actually have a room id assigned (hopefully)
        self.room_id = data

    def disconnect(self, close_data):
        """
        Should be called when the websocket closes for any reason.
        In reality, there are a few edge cases where it doesn't. See
        """
        log.debug("{} disconnect {}".format(self.room_id, close_data))
        if getattr(self, "proc", None):
            self.proc.terminate()

        raise StopConsumer

    def handle_outgoing(self, data):
        # with the data we recieve from the GameScheduler,
        # send it through the websocket
        log.debug("Got data {}".format(data))
        str_data = data.decode('utf-8').strip()
        if getattr(self, 'room_id', False):
            self.send(text_data=str_data)
        else:
            self.room_id = str_data

    def handle_incoming(self, content):
        content['room_id'] = self.room_id
        data = json.dumps(content).encode('utf-8')
        self.transport.write(data)

    def recieve_json(self, content):
        # with the data we recieve from the websocket,
        # send it to the GameScheduler
        log.debug("Recieving json {}".format(content))
        if getattr(self, 'room_id', False):
            self.handle_incoming(content)
        else:
            log.warn("Recieved data before we could get a room id! ignoring...")


class GamePlayingConsumer(GameConsumer):
    black_ai = None
    white_ai = None
    timelimit = 5

    def connect(self):
        super().connect()
        # parse URL
        self.black_ai = self.scope['url_route']['kwargs'].get('black', None)
        self.white_ai = self.scope['url_route']['kwargs'].get('white', None)
        self.timelimit = safe_int(self.scope['url_route']['kwargs'].get('t', None))

        if self.black_ai is None or self.white_ai is None:
            log.warn("Got invalid play_request from client!")
            self.accept()
            self.send_json({'type': "gameerror", 'error':"Error: You didn't specify the AIs to play in the websocket url!"})
            self.send_json({'type': "gameend", 'winner': "?", 'forfeit': True})
            self.close()
        else:
            self.accept()

    def first_init(self, data):
        # send initial playing request
        super().__init__(data)
        content = {
            'type': "play_request",
            'black': self.black_ai,
            'white': self.white_ai,
            't': self.timelimit,
            'room_id': self.room_id,
        }
        encoded_content = json.dumps(content).encode('utf-8')
        self.transport.write(encoded_content)

class GameWatchingConsumer(GameConsumer):
    watching = None

    def connect(self):
        super().connect()
        # parse URL
        self.watching = self.scope['url_route']['kwargs'].get('watching', None)

        if self.watching is None:
            log.warn("Got invalid watch_request from client!")
            self.accept()
            self.send_json({'type': "gameerror", 'error':"Error: You didn't specify which game to watch in the websocket url!"})
            self.send_json({'type': "gameend", 'winner': "?", 'forfeit': True})
            self.close()
        else:
            self.accept()

    def first_init(self, data):
        # send initial watching request
        content = {
            'type': 'watch_request',
            'watching': self.watching,
            'room_id': self.room_id,
        }
        encoded_content = json.dumps(content).encode('utf-8')
        self.transport.write(encoded_content)
