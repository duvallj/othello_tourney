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
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async, async_to_sync
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer

import logging

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
        await self.accept()

    async def receive_json(self, content):
        """
        Called when we get a message from the client.
        The only message we care about is "move_reply",
        which should only get sent if we provoke it.
        """
        log.debug("{} received json {}".format(self.main_room.room_id, content))
        msg_type = content.get('msg_type', None)
        if msg_type == "movereply":
            pass
        elif msg_type == "prequest":
            pass
        elif msg_type == "wrequest":
            pass
        log.debug("{} successfully handled {}".format(self.main_room.room_id, msg_type))

    async def disconnect(self, close_data):
        """
        Should be called when the websocket closes for any reason.
        In reality, there are a few edge cases where it doesn't. See

        """
        log.debug("{} disconnect {}".format(self.main_room.room_id, close_data))
        if getattr(self, "proc", None):
            self.proc.terminate()

        raise StopConsumer

    def board_update(self, event):
        """
        Called when there is an update on the board
        that we need to send to the client
        """
        log.debug("{} board_update {}".format(self.main_room.room_id, event))
        self.send_json({
            'msg_type': 'reply',
            'board': event.get('board', ""),
            'tomove': event.get('tomove', "?"),
            'black': event.get('black', settings.OTHELLO_AI_UNKNOWN_PLAYER),
            'white': event.get('white', settings.OTHELLO_AI_UNKNOWN_PLAYER),
            'bSize': '8',
        })

    def move_request(self, event):
        """
        Called when the game wants the user to input a move.
        Sends out a similar call to the client
        """
        log.debug("{} move_request {}".format(self.main_room.room_id, event))
        self.send_json({'msg_type':"moverequest"})

    def move_reply(self, event):
        """
        Called when a client sends a move after the game loop pauses for user input.
        Sends the received move back to the game.
        """
        if self.comm_queue:
            log.debug("{} move_reply {}".format(self.main_room.room_id, event))
            self.comm_queue.put(event.get('move', -1))
        else:
            # We are just watching a game
            pass

    def game_end(self, event):
        """
        Called when the game has ended, tells client that message too.
        Really should log the result but doesn't yet.
        """
        log.debug("{} game_end {}".format(self.main_room.room_id, event))
        self.send_json({
            'msg_type': "gameend",
            'winner': event.get('winner', "?"),
            'forfeit': event.get('forfeit', False),
        })

    def game_error(self, event):
        """
        Called whenever the AIs/server errors out for whatever reason.
        Could be used in place of game_end
        """
        log.debug("{} game_error {}".format(self.main_room.room_id, event))
        self.send_json({
            'msg_type': "gameerror",
            'error': event.get('error', "No error"),
        })
