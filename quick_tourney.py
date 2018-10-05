import os
import django
from channels.routing import get_default_application
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "othello.settings")
django.setup()
application = get_default_application()

NUM_CHECKPOINTS = 30

from othello.apps.tournament.consumers import TournamentRunner
import queue
import pickle

class AlphaZeroTournamentRunner(TournamentRunner):
    def start(self):
        self.results = []
        self.game_queue = queue.Queue()
        for i in range(1, NUM_CHECKPOINTS+1):
            self.game_queue.put(('random', 'alphazero{}'.format(i)))
            self.game_queue.put(('alphazero{}'.format(i), 'random'))

        self.start_game(*self.game_queue.get())

    def end(self):
        print(self.results)
        with open('aztr.pkl', 'wb') as f:
            pickle.dump(self.results, f)
