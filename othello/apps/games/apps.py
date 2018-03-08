from django.apps import AppConfig

class GamesConfig(AppConfig):
    name = 'othello.apps.games'
    def ready(self):
        from .models import Room
        Room.objects.all().delete()
