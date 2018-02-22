from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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
    pass
    
@login_required
def logout_view(request):
    pass