from django.shortcuts import render
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.contrib.auth.signals import user_logged_in

from ..users.models import User

def index_view(request):
    return render(request, "index.html")
    
@login_required
def upload_view(request):
    if request.method == "POST":
        # verify, upload file
        return render(request, "upload_complete.html")
    # probably need to do something with username here...
    return render(request, "upload.html")
    
def login_view(request):
    return render(request, "login.html")
    
    
def grant_access_token(sender, user, request, **kwargs):
    request.user.access_token = get_random_string(24)
    request.user.save()
    
user_logged_in.connect(grant_access_token)
    
def logout_view(request):
    if request.user.is_authenticated():
        request.user.access_token = None
        request.user.save()
    logout(request)
    return redirect("index")