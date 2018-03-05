from django.conf import settings
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import sync_to_async, async_to_sync
from channels.db import database_sync_to_async

import logging as log
from multiprocessing import Process, Queue

from .utils import make_new_room, get_all_rooms
from .worker_utils import safe_int, safe_float
from .worker import GameRunner

class GameServingConsumer(JsonWebsocketConsumer):
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
        self.rooms.add(room)
        self.main_room = room
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
            print("Got prequest with data {}".format(content))
            print(self.main_room.room_id)
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
            pass
        
    def disconnect(self, close_data):
        """
        Called when the websocket closes for any reason.
        """
        self.proc.terminate()
        
    # Handlers for messages sent over the channel layer
    
    def create_game(self, event):
        """
        Called when a client wants to create a game.
        Actually starts running the game as well
        """
        print("Create game called")
        self.game = GameRunner(self.main_room.room_id)
        self.game.black = event["black"]
        self.game.white = event["white"]
        self.game.timelimit = event["timelimit"]
        self.comm_queue = Queue()
        self.proc = Process(target=self.game.run, args=(self.comm_queue,))
        self.proc.start()
        
    def join_game(self, event):
        """
        Called when a client wants to join an existing game.
        """
        pass
        
    def board_update(self, event):
        """
        Called when there is an update on the board
        that we need to send to the client
        """
        print(event)
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
        self.send_json({'msg_type':"moverequest"})
        
    def move_reply(self, event):
        """
        Called when a client sends a move after the game loop pauses for user input.
        Sends the received move back to the game.
        """
        self.comm_queue.put(event.get('move', -1))
        
    def game_end(self, event):
        """
        Called when the game has ended, tells client that message too.
        Really should log the result but doesn't yet.
        """
        print(event)
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
        pass