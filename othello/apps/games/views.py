from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def play_view(request):
    return render(request, "play.html")
    
def watch_view(request):
    return render(request, "watch.html")
    
def about_view(request):
    return render(request, "about.html")
    
def about_uploading_view(request):
    return render(request, "about_uploading.html")
    
def ai_list_view(request):
    return HttpResponse("random", content_type="text/plain")
    
def game_list_view(request):
    return HttpResponse("null,null,null,5", content_type="text/plain")