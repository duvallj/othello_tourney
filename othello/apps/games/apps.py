from django.apps import AppConfig

class GamesConfig(AppConfig):
    name = 'othello.apps.games'
    def ready(self):
        from .models import Room
        try:
            Room.objects.all().delete()
        except:
            pass
