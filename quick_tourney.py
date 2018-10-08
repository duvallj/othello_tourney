import os
import asyncio
import django
from channels.routing import get_default_application
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "othello.settings")
django.setup()
application = get_default_application()

NUM_CHECKPOINTS = 1

from othello.apps.tournament.consumers import TournamentRunner
import queue
import pickle

class AlphaZeroTournamentRunner(TournamentRunner):
        
    async def start(self):
        print("started")
        self.results = []
        self.game_queue = queue.Queue()
        for i in range(1, NUM_CHECKPOINTS+1):
            self.game_queue.put(('random', 'random'))#'alphazero{}'.format(i)))
            self.game_queue.put(('random', 'random'))#'alphazero{}'.format(i), 'random'))

        await self.start_game(*self.game_queue.get())

    def end(self):
        print(self.results)
        with open('aztr.pkl', 'wb') as f:
            pickle.dump(self.results, f)
        print("Done, safe to kill script now")
            
if __name__ == "__main__":
    a = AlphaZeroTournamentRunner(None)
    a.post_init(5)
    
    async def nothing(): return {"type": "move.reply", "move": "-1"}
    tasks = [
        asyncio.ensure_future(a(nothing, nothing)),
        asyncio.ensure_future(a.start()),
    ]
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
    
