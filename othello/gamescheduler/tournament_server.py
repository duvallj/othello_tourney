"""
Read server.py first, and heed the warning there
"""

import asyncio
from threading import Lock
import queue
import logging
import itertools

from .server import Room, GameScheduler
from .utils import generate_id
from .othello_core import BLACK, WHITE, EMPTY

log = logging.getLogger(__name__)

class TournamentScheduler(GameScheduler):
    """
    A subclass that doesn't allow anyone to make new games, and
    is instead started with a list of initial games to start running.
    Logs results of tournament to CSV file for easy processing,
    either by Django shell or other method.
    """

    """
    Methods needed to be implemented by the subclass:
      * populate_game_queue
      * check_game_queue
    Exposed internal variables:
      * ai_list: list of AIs, supposedly in order from strongest to weakest
      * timelimit: float
      * max_games: int, maximum number of games to play at once
      * num_games: int, current number of games running
      * results: list
      * results_lock: threading.Lock
    Using add_new_game to add new games to the game queue
    """

    def __init__(self, loop, completed_callback=lambda *x:None, record_callback=lambda *y:None, ai_list=[], timelimit=5, max_games=2):
        super().__init__(loop)

        self.completed_callback = completed_callback
        self.record_callback = record_callback
        self.ai_list = ai_list
        self.timelimit = timelimit
        self.max_games = max_games
        self.num_games = 0
    
        self.game_queue = queue.Queue()
        self.results = []
        self.results_lock = Lock()

        # populate queue with initial matchups to play
        # Should also start to play games on its own
        self.populate_game_queue()

    def add_new_game(self, black, white, timelimit=None):
        if timelimit is None:
            self.game_queue.put_nowait((black, white, self.timelimit))
        else:
            self.game_queue.put_nowait((black, white, timelimit))

    def populate_game_queue(self):
        # Called in __init__, should be defined by subclasses in order to start
        # the initial matches
        raise NotImplementedError

    def check_game_queue(self):
        # Called after each game ends, when the result has been recorded as
        # the last element in self.results
        raise NotImplementedError

    def play_game(self, parsed_data, room_id):
        # send an error message back telling them they can't play
        log.warn("Client {} tried to play during a tournament".format(room_id))
        self.game_error({'error': "You cannot start a game during a tournament."}, room_id)
        self.game_end(dict(), room_id)

    def play_tournament_game(self, black, white, timelimit):
        self.loop.call_soon_threadsafe(self._play_tournament_game, black, white, timelimit)

    def play_next_game(self):
        if not self.game_queue.empty():
            self.play_tournament_game(*self.game_queue.get_nowait())
            self.num_games += 1
            
            if self.num_games > self.max_games:
                log.warn("Playing more games at a time than allowed...")


    def _play_tournament_game(self, black, white, timelimit):
        log.info("Playing next game: {} v {}".format(black, white))
        new_id = generate_id()
        # extremely low chance to block, ~~we take those~~
        while new_id in self.rooms: new_id = generate_id()
        room = Room()
        room.id = new_id
        self.rooms[new_id] = room
        log.debug("Creating new room id {}".format(new_id))

        self.play_game_actual(black, white, timelimit, new_id)

    def game_end(self, parsed_data, room_id):
        log.debug("Overridded game_end called")
        # log result
        board = parsed_data.get('board', "")
        forfeit = parsed_data.get('forfeit', False)
        winner = parsed_data.get('winner', EMPTY)
        black_score = board.count(BLACK)
        white_score = board.count(WHITE)
        black_ai = self.rooms[room_id].black_ai
        white_ai = self.rooms[room_id].white_ai

        with self.results_lock:
            result = (
                black_ai, white_ai, black_score, white_score, winner, int(forfeit),
            )

            self.results.append(result)

        log.debug("Added to results: {}".format(result))

        super().game_end(parsed_data, room_id)
        self.num_games -= 1

        # handle putting new games into queue, if necessary
        self.check_game_queue()

    def tournament_end(self):
        log.info("Tournament completed! Returning results...")
        self.loop.call_soon_threadsafe(self.completed_callback, self.results, self.results_lock)

class RRTournamentScheduler(TournamentScheduler):
    def populate_game_queue(self):
        for black, white in itertools.permutations(self.ai_list, 2):
            self.add_new_game(black, white)
        
        while self.num_games < self.max_games and not self.game_queue.empty():
            self.play_next_game()
    
    def check_game_queue(self):
        if self.game_queue.empty():
            self.tournament_end()
        else:
            self.play_next_game()


class BracketTournamentScheduler(TournamentScheduler):
    def populate_game_queue(self):
        # All the logic is handled in the other method
        self.remaining_ai_list = self.ai_list.copy()
        self.last_result_recorded = -1
        self.add_games_from_remaining()
        while self.num_games < self.max_games and not self.game_queue.empty():
            self.play_next_game()

    def add_games_from_remaining(self):
        self.regenerate_win_data()

        # If we have an even number, play everyone
        if len(self.remaining_ai_list) % 2 == 0:
            for i in range(len(self.remaining_ai_list)//2):
                ai1 = self.remaining_ai_list[i]
                ai2 = self.remaining_ai_list[len(self.remaining_ai_list)-i-1]
                self.add_new_game(ai1, ai2)
                self.add_new_game(ai2, ai1)
        # If we have an odd number, let the first seed have a bye
        else:
            for i in range(1, len(self.remaining_ai_list)//2+1):
                ai1 = self.remaining_ai_list[i]
                ai2 = self.remaining_ai_list[len(self.remaining_ai_list)-i]
                self.add_new_game(ai1, ai2)
                self.add_new_game(ai2, ai1)
            # Also don't forget to give first person a bye
            self.results.append((self.remaining_ai_list[0],"BYE",1,0,BLACK,0))
            self.results.append(("BYE",self.remaining_ai_list[0],0,1,WHITE,0))


    def regenerate_win_data(self):
        self.differential_dict = dict()

    def check_game_queue(self):
        # Record result of game
        if len(self.results)-1 > self.last_result_recorded:
            black_ai, white_ai, black_score, white_score, winner, forfeit = self.results[-1]
            if forfeit:
                if winner == BLACK:
                    log.info("Forfeit by {} as white versus {}".format(white_ai, black_ai))
                    self.differential_dict[white_ai] = -float('inf')
                elif winner == WHITE:
                    log.info("Forfeit by {} as black versus {}".format(black_ai, white_ai))
                    self.differential_dict[black_ai] = -float('inf')
                else:
                    log.error("Forfeit in {} vs {} but no winner? Disqualifying both".format(black_ai, white_ai))
                    self.differential_dict[black_ai] = -float('inf')
                    self.differential_dict[white_ai] = -float('inf')
            else:
                black_diff = self.differential_dict.get(black_ai, 0)
                white_diff = self.differential_dict.get(white_ai, 0)
                self.differential_dict[black_ai] = black_diff + black_score - white_score
                self.differential_dict[white_ai] = white_diff + white_score - black_score
            
            self.last_result_recorded += 1
            log.debug("Result of {} vs {} recorded".format(black_ai, white_ai))

        # Only create next stage if the current one is finished
        if self.game_queue.empty() and self.num_games == 0:
            log.info("Tournament stage ended, starting new one")
            # First, recalculate remaining AIs based on results from last time
            new_remaining_ai_list = []
            for i in range(len(self.remaining_ai_list)):
                ai = self.remaining_ai_list[i]
                if self.differential_dict.get(ai, 0) > 0:
                    new_remaining_ai_list.append(ai)
                elif i < len(self.remaining_ai_list)//2 and self.differential_dict.get(ai, 0) == 0:
                    # In case of tie, higher seeded AI advances
                    new_remaining_ai_list.append(ai)
                else:
                    # Don't add them
                    pass

            self.remaining_ai_list = new_remaining_ai_list
            log.info("AI in next stage: {}".format(self.remaining_ai_list))
            # If we only have one AI left, end tournament
            if len(self.remaining_ai_list) == 1:
                self.tournament_end()
                return

            self.add_games_from_remaining()

        while self.num_games < self.max_games and not self.game_queue.empty():
            self.play_next_game()
