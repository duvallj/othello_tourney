from django.apps import AppConfig


class TournamentConfig(AppConfig):
    name = 'othello.apps.tournament'
    def ready(self):
        pass
    #label = 'othello.apps.tournament'
