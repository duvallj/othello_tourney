from django.utils.crypto import get_random_string

from .models import Room

def gen_room_id():
    """
    Generates a new room id
    """
    return get_random_string(length=32)

def make_new_room():
    """
    Makes a new room. Usually called when a client connects via websocket
    Really should check for duplicates, but doesn't
    """
    room_id = gen_room_id()
    room, _ = Room.objects.get_or_create(room_id=room_id)
    pass
    
def get_all_rooms():
    """
    Returns a list of all available rooms
    """
    pass
    
def delete_room(room_id):
    """
    Deletes a room. Usually called when client disconnects their websocket
    """
    pass