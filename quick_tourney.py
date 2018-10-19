import os
import asyncio
import django
from channels.routing import get_default_application
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "othello.settings")
django.setup()
application = get_default_application()

NUM_CHECKPOINTS = 80
START_CHECKPOINT = 53
OTHER_AIS = ['duv', '2019ssaxena', '2019vnguyen']

from othello.apps.tournament.consumers import TournamentRunner
import queue
import pickle

class AlphaZeroTournamentRunner(TournamentRunner):
    def save(self):
        with open('aztr2-3.pkl', 'wb') as f:
            pickle.dump(self.results, f)
    
    def game_end(self, event):
        super().game_end(event)
        print("saving...")
        self.save()
        print("saved")

    async def start(self):
        print("started")
        self.results = []
        self.game_queue = queue.Queue()
        for i in range(START_CHECKPOINT, NUM_CHECKPOINTS+1):
            if os.path.isfile(os.path.join(
                os.getcwd(), 
                'students/alphazero/temp2/checkpoint_{}.pth.tar'.format(i)
            )):
                for ai in OTHER_AIS:
                    self.game_queue.put((ai, 'alphazero{}'.format(i)))
                    self.game_queue.put(('alphazero{}'.format(i), ai))

        await self.start_game(*self.game_queue.get())

    def end(self):
        self.save()
        print("Done, safe to kill script once \"saved\" appears")
            
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
    
