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

import logging

log = logging.getLogger(__name__)

class GameConsumer(AsyncJsonWebsocketConsumer):
    """
    The consumer the handle websocket connections with game clients.

    Does no actual game running itself, just provides an interface to the tasks that do.

    Just for reference, it seems a new one of these is created for each new client.
    """


    # #### Websocket event handlers

    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        Creates a new room (with id) for the client and adds them to that room.
        """

        # Make a new storage for rooms
        self.rooms = set()

        # Make and add a new room
        room = make_new_room()
        self.rooms.add(room.room_id)
        self.main_room = room
        log.debug("Made new room {} for channel {}, now joining...".format(room.room_id, self.channel_name))
        async_to_sync(self.channel_layer.group_add)(
            room.room_id,
            self.channel_name,
        )
        self.accept()

    def receive_json(self, content):
        """
        Called when we get a message from the client.
        The only message we care about is "move_reply",
        which should only get sent if we provoke it.
        """
        log.debug("{} received json {}".format(self.main_room.room_id, content))
        msg_type = content.get('msg_type', None)
        if msg_type == "movereply":
            async_to_sync(self.channel_layer.group_send)(
                self.main_room.room_id,
                {
                    'type': "move.reply",
                    'move': safe_int(content.get('move', "-1"))
                },
            )
        elif msg_type == "prequest":
            async_to_sync(self.channel_layer.group_send)(
                self.main_room.room_id,
                {
                    'type': "create.game",
                    'black': content.get('black', settings.OTHELLO_AI_UNKNOWN_PLAYER),
                    'white': content.get('white', settings.OTHELLO_AI_UNKNOWN_PLAYER),
                    'timelimit': safe_float(content.get('timelimit', "5.0"))
                },
            )
        elif msg_type == "wrequest":
            async_to_sync(self.channel_layer.group_send)(
                self.main_room.room_id,
                {
                    'type': "join.game",
                    'room': content.get('watching', self.main_room.room_id),
                },
            )
        log.debug("{} successfully handled {}".format(self.main_room.room_id, msg_type))

    def disconnect(self, close_data):
        """
        Should be called when the websocket closes for any reason.
        In reality, there are a few edge cases where it doesn't. See

        """
        log.debug("{} disconnect {}".format(self.main_room.room_id, close_data))
        if getattr(self, "proc", None):
            self.proc.terminate()
        for room in self.rooms:
            async_to_sync(self.channel_layer.group_discard)(
                room,
                self.channel_name,
            )
        delete_room(self.main_room.room_id)

    # Handlers for messages sent over the channel layer

    def create_game(self, event):
        """
        Called when a client wants to create a game.
        Actually starts running the game as well
        """
        log.debug("{} create_game {}".format(self.main_room.room_id, event))
        self.game = GameRunner(self.main_room.room_id)
        self.game.black = event["black"]
        self.game.white = event["white"]
        self.game.timelimit = event["timelimit"]

        self.main_room.black = event["black"]
        self.main_room.white = event["white"]
        self.main_room.timelimit = safe_float(event["timelimit"])
        self.main_room.playing = True
        self.main_room.save()

        # So it turns out channels doesn't like doing async_to_sync stuff
        # from inside forked processes, so we need to use spawned ones instead.
        ctx = mp.get_context('spawn')
        self.comm_queue = ctx.Queue()
        self.proc = ctx.Process(target=self.game.run, args=(self.comm_queue,))
        self.proc.start()

    def join_game(self, event):
        """
        Called when a client wants to join an existing game.
        """
        log.debug("{} join_game {}".format(self.main_room.room_id, event))
        room_id = event.get('room', self.main_room.room_id)
        self.rooms.add(room_id)
        async_to_sync(self.channel_layer.group_add)(
            room_id,
            self.channel_name,
        )
        self.comm_queue = None
        self.proc = None

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
