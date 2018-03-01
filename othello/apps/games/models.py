from django.db import models
from django.conf import settings

class Room(models.Model):
    """
    A room for games to happen in. Every client automatically gets a room,
    its just that they can request to join other rooms to view other games.
    """
    
    # Room id, used for finding the room
    room_id = models.CharField(max_length=OTHELLO_ROOM_ID_LEN, primary_key=True)
    
    # Players
    black = models.CharField(max_length=64, null=True)
    white = models.CharField(max_length=64, null=True)
    
    # Time limit
    timelimit = models.FloatField(null=True)
