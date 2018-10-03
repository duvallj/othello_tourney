from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^tournament/$', views.tournament_view, name="tournament"),
]
