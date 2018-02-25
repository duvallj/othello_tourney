from django.shortcuts import render, redirect
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.contrib.auth.signals import user_logged_in
from django.conf import settings

from ..users.models import User
from .forms import UploadFileForm

import os

def index_view(request):
    return render(request, "index.html")
    
def handle_uploaded_file(user, file):
    fdir = os.path.join(settings.MEDIA_ROOT, user.username)
    os.makedirs(fdir, mode=0o755, exist_ok=True)
    with open(os.path.join(fdir, 'strategy.py'), 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
@login_required
def upload_view(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.user, request.FILES['code'])
            return render(request, "upload_complete.html")
    else: 
        form = UploadFileForm()
    return render(request, "upload.html", {'form': form})
    
def login_view(request):
    return render(request, "login.html")
    
def grant_access_token(sender, user, request, **kwargs):
    request.user.access_token = get_random_string(24)
    request.user.save()
    
user_logged_in.connect(grant_access_token)
    
def logout_view(request):
    if request.user.is_authenticated:
        request.user.access_token = None
        request.user.save()
    logout(request)
    return redirect("index")