from django.conf import settings
from channels.consumer import SyncConsumer
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async, async_to_sync
from channels.db import database_sync_to_async

from ..games.utils import make_new_room, get_all_rooms, delete_room
#from .utils import make_new_tournament, delete_tournament
from ..games.worker_utils import safe_int, safe_float
from ..games.worker import GameRunner

import logging
import multiprocessing as mp

log = logging.getLogger(__name__)

class TournamentRunner(SyncConsumer):
    #def __init__(self, player_list, format, num_games, concurrent_games, *args, **kwargs):
        
    def post_init(self, timelimit):
        """self.tournament = make_new_tournament()
        self.tournament.player_list = player_list
        self.tournament.format = format
        self.tournament.num_games = num_games
        self.tournament.concurrent_games = concurrent_games
        self.tournament.results = []
        self.tournament.save()"""
        self.timelimit = timelimit
        self.games = dict()
        self.game_queue = None

    ### Methods for compatability w/ results from GameServingConsumer

    def create_game(self, event): pass
    def join_game(self, event): pass
    def board_update(self, event): pass # might want to use later on
    def move_request(self, event): pass
    def move_reply(self, event): pass

    def game_end(self, event):
        rid = event['room_id']
        print(self.games[rid])
        self.results.append((
            event['winner'],
            event['board'],
            {   '@': self.games[rid]['room'].black,
                'o': self.games[rid]['room'].white, },
        ))
        if self.games[rid]['proc']: self.games[rid]['proc'].terminate()
        async_to_sync(self.channel_layer.group_discard)(
            rid,
            self.channel_name
        )
        #print(rid, self.games[rid]['room'].room_id)
        #delete_room(rid)
        del self.games[rid]

        if self.game_queue and not self.game_queue.empty():
            async_to_sync(self.start_game)(*self.game_queue.get())
        else:
            self.end()

    def game_error(self, event): log.error(event.get('error', ''))

    ### End compat methods

    async def start_game(self, black, white):
        room = make_new_room()
        """log.debug("Made new room {} for tournament {}".format(
            room.room_id,
            self.tournament.tournament_id
        ))"""

        game = GameRunner(room.room_id)
        game.black = black
        game.white = white
        game.timelimit = self.timelimit

        room.black = black
        room.white = white
        room.timelimit = self.timelimit
        room.playing = True
        room.save()

        # Same as as games/consumers.py, need to have spawn
        # to not screw up other async stuff
        ctx = mp.get_context('spawn')
        comm_queue = ctx.Queue()
        proc = ctx.Process(target=game.run, args=(comm_queue,))
        proc.start()

        self.games[room.room_id] = {
            'room': room,
            'game': game,
            'proc': proc,
            'comm_queue': comm_queue,
        }

        await self.channel_layer.group_add(
            room.room_id,
            self.channel_name
        )


    def start(self):
        self.results = []
        for x in range(num_games):
            pass

    def end(self):
        pass

    def stop(self):
        self.end()
        pass
