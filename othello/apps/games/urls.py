from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^play$', views.play_view, name='play'),
    url(r'^watch$', views.watch_view, name='watch'),
    url(r'^about$', views.about_view, name='about'),
    url(r'^about_uploading$', views.about_uploading_view, name='about_uploading'),
    url(r'^list/ais', views.ai_list_view, name="ai_list"),
    url(r'^list/games', views.game_list_view, name="game_list"),
]