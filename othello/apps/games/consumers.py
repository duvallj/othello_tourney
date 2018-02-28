from channels.generic.websocket import JsonWebsocketConsumer

from .utils import make_new_room, get_all_rooms
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
        
    def receive_json(self, content):
        """
        Called when we get a message from the client.
        The only message we care about is "move_reply",
        which should only get sent if we provoke it.
        """
        pass
        
    def disconnect(self, close_data):
        """
        Called when the websocket closes for any reason.
        """
        pass
        
    # Handlers for messages sent over the channel layer
    
    def create_game(self, event):
        """
        Called when a client wants to create a game.
        Actually starts running the game as well
        """
        pass
        
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
        pass
        
    def move_request(self, event):
        """
        Called when the game loop pauses for user input.
        Sends a similarly-named event out, and sets a flag
        saying we are waiting for a reply.
        """
        pass
        
    def game_end(self, event):
        """
        Called when the game has ended, tells client that message too.
        Really should log the result but doesn't yet.
        """
        pass