from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings

from .utils import get_all_rooms

import os

def play_view(request):
    return render(request, "play.html")
    
def watch_view(request):
    return render(request, "watch.html")
    
def about_view(request):
    return render(request, "about.html")
    
def about_uploading_view(request):
    return render(request, "about_uploading.html")
    
def ai_list_view(request):
    student_folder = settings.MEDIA_ROOT
    folders = os.listdir(student_folder)
    possible_names =  [x for x in folders if \
        x != '__pycache__' and x != 'public' and \
        os.path.isdir(os.path.join(student_folder, x))
    ]
    return HttpResponse("\n".join(possible_names), content_type="text/plain")
    
def game_list_view(request):
    rooms = get_all_rooms()
    data_list = [
        "{},{},{},{}".format(
            room.room_id,
            room.black,
            room.white,
            room.timelimit
        ) 
        for room in rooms
     ]
    return HttpResponse("\n".join(data_list), content_type="text/plain")