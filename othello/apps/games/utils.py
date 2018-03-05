from django.utils.crypto import get_random_string
from django.conf import settings

from .models import Room

def gen_room_id():
    """
    Generates a new room id
    """
    return get_random_string(length=settings.OTHELLO_ROOM_ID_LEN)

def make_new_room():
    """
    Makes a new room. Usually called when a client connects via websocket
    Really should check for duplicates, but doesn't
    """
    print("make new room called")
    room_id = gen_room_id()
    print("room id created")
    # OTHELLO_ROOM_ID_LEN should really be long enough that this never triggers
    while Room.objects.filter(room_id=room_id).exists(): room_id = gen_room_id()
    print("Good room id found")
    room, _ = Room.objects.get_or_create(room_id=room_id)
    print("created the room")
    return room
    
def get_all_rooms():
    """
    Returns a list of all available rooms
    """
    return Room.objects.all()
    
def delete_room(room_id):
    """
    Deletes a room. Usually called when client disconnects their websocket
    """
    pass