"""othello URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from .apps.auth import views as auth_views
from .apps.games import views as game_views


urlpatterns = [
    url('', include('social_django.urls', namespace='social')),
    url(r'^$', auth_views.index_view, name='index'),
    url(r'^upload$', auth_views.upload_view, name='upload'),
    url(r'^play$', game_views.play_view, name='play'),
    url(r'^watch$', game_views.watch_view, name='watch'),
    url(r'^about$', game_views.about_view, name='about'),
    url(r'^about_uploading$', game_views.about_uploading_view, name='about_uploading'),
    url(r'^login/$', auth_views.login_view, name='login'),
    url(r'^logout/$', auth_views.login_view, name='logout'),
    url(r'^admin/', admin.site.urls),
]
