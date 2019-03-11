import os

from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from asgiref.sync import async_to_sync
import json

from .utils import get_playing_rooms


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
    # Using the filesystem as a database for which students
    # have uploaded. kind of hacky, but works well
    folders = os.listdir(student_folder)
    possible_names = [x for x in folders if
        x != '__pycache__' and x != 'public' and
        os.path.isdir(os.path.join(student_folder, x))
    ]
    possible_names = sorted(possible_names)
    return HttpResponse("\n".join(possible_names), content_type="text/plain")

def game_list_view(request):
    rooms = async_to_sync(get_playing_rooms)()
    print(rooms)
    data_list = [
        "{},{},{},{}".format(
            room,
            rooms[room][0], # black
            rooms[room][1], # white
            rooms[room][2], # timelimit
        )
        for room in rooms
    ]
    return HttpResponse("\n".join(data_list), content_type="text/plain")
