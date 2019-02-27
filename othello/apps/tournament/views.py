from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings

from ..users.models import User
from .forms import StartTournamentForm

def tournament_info_view(request):
    return render(request, "tournament_info.html")

def manage_all_tournaments_view(request):
    return render(request, "tournament_manage.html")

@login_required
def create_tournament_view(request):
    if request.method == "POST":
        form = EditTournamentForm(request.POST, request.FILES)
        if form.is_valid():
            # Start tournament
            return render(request, "tournament_started.html")
    else:
        form = EditTournamentForm()
    return render(request, "tournament_create.html", {'form': form, 'new': True})

@login_required
def manage_one_tournament_view(request):
    if request.method == "POST":
        form = EditTournamentForm(request.POST, request.FILES)
        if form.is_valid():
            # Stop tournament
            # Edit tournament
            # Start tournament
            return render(request, "tournament_started.html")
    else:
        form = EditTournamentForm()
    return render(request, "tournament_create.html", {'form': form, 'new': False})
