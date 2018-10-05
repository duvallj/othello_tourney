from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^tournament/list$', views.tournament_info_view, name="tournament list"),
]
