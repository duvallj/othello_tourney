from django.shortcuts import render

# Create your views here.

def play_view(request):
    return render(request, "play.html")
    
def watch_view(request):
    return render(request, "watch.html")
    
def about_view(request):
    return render(request, "about.html")
    
def about_uploading_view(request):
    return render(request, "about_uploading.html")