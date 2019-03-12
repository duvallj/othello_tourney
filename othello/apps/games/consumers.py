"""
##########################
#         WARNING        #
##########################

You should not read this or any file in gamescheduler without first looking at
the file `run_ai_layout.txt' at the root of this repo. It contains the basic
layout for how everything fits together to run a game, which is really hard to
understand otherwise.

Debuggig any of this is not for the faint of heart. Consider yourself warned.
"""

from django.conf import settings
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async, async_to_sync
from channels.exceptions import StopConsumer
import asyncio
from concurrent.futures import ThreadPoolExecutor

import logging
import json

from ...gamescheduler.client import game_scheduler_client_factory
from ...gamescheduler.utils import safe_int

log = logging.getLogger(__name__)

class GameConsumer(AsyncJsonWebsocketConsumer):
    """
    The consumer the handle websocket connections with game clients.

    Does no actual game running itself, just provides an interface to the tasks that do.

    Just for reference, it seems a new one of these is created for each new client.
    """

    # #### Websocket event handlers

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        self.loop = asyncio.get_event_loop()
        self.transport, self.protocol = await self.loop.create_connection(
            game_scheduler_client_factory(self.loop, self.first_init, self.handle_outgoing),
            host=settings.SCHEDULER_HOST,
            port=settings.SCHEDULER_PORT
        )
        self.room_id = None

    def first_init(self, data):
        log.debug("first_init {}".format(data))
        # called when we actually have a room id assigned (hopefully)
        self.room_id = data

    async def disconnect(self, close_data):
        """
        Should be called when the websocket closes for any reason.
        In reality, there are a few edge cases where it doesn't. See
        """
        log.debug("{} disconnect {}".format(self.room_id, close_data))
        self.transport.close()

        raise StopConsumer

    async def handle_outgoing(self, data):
        # with the data we recieve from the GameScheduler,
        # send it through the websocket
        log.debug("Got data {}".format(data))
        if getattr(self, 'room_id', False):
            await self.send(text_data=data)
        else:
            self.room_id = data

    def handle_incoming(self, content):
        content['room_id'] = self.room_id
        data = json.dumps(content).encode('utf-8')
        self.transport.write(data)

    async def recieve_json(self, content):
        # with the data we recieve from the websocket,
        # send it to the GameScheduler
        log.debug("Recieving json {}".format(content))
        if getattr(self, 'room_id', False):
            self.handle_incoming(content)
        else:
            log.info("Recieved data before we could get a room id! ignoring...")

    # just in case of wonkiness
    def __del__(self):
        if getattr(self, 'transport', None):
            self.transport.close()


class GamePlayingConsumer(GameConsumer):
    black_ai = None
    white_ai = None
    timelimit = 5

    async def connect(self):
        await super().connect()
        # parse URL
        self.black_ai = self.scope['url_route']['kwargs'].get('black', None)
        self.white_ai = self.scope['url_route']['kwargs'].get('white', None)
        self.timelimit = safe_int(self.scope['url_route']['kwargs'].get('t', None))

        if self.black_ai is None or self.white_ai is None:
            log.warn("Got invalid play_request from client!")
            await self.accept()
            await self.send_json({'type': "gameerror", 'error':"Error: You didn't specify the AIs to play in the websocket url!"})
            await self.send_json({'type': "gameend", 'winner': "?", 'forfeit': True})
            await self.close()
        else:
            await self.accept()

    def first_init(self, data):
        # send initial playing request
        super().first_init(data)
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

    async def connect(self):
        await super().connect()
        # parse URL
        self.watching = self.scope['url_route']['kwargs'].get('watching', None)

        if self.watching is None:
            log.warn("Got invalid watch_request from client!")
            await self.accept()
            await self.send_json({'type': "gameerror", 'error':"Error: You didn't specify which game to watch in the websocket url!"})
            await self.send_json({'type': "gameend", 'winner': "?", 'forfeit': True})
            await self.close()
        else:
            await self.accept()

    def first_init(self, data):
        # send initial watching request
        super().first_init(data)
        content = {
            'type': 'watch_request',
            'watching': self.watching,
            'room_id': self.room_id,
        }
        encoded_content = json.dumps(content).encode('utf-8')
        self.transport.write(encoded_content)
