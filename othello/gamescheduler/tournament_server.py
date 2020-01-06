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
from .othello_core import BLACK, WHITE, EMPTY, OUTER
from ..apps.tournament.models import GameModel, SetModel, MoveModel
from ..apps.tournament.utils import add_game_to_set, calc_set_winner, \
    get_player, count_completed_games, create_set, safely_call

log = logging.getLogger(__name__)

class AutomaticGameScheduler(GameScheduler):
    """
    A subclass that doesn't allow anyone to make new games, and
    is instead started with a list of initial games to start running.
    """

    """
    Methods needed to be implemented by the subclass:
      * populate_game_queue()
      * check_game_queue()
    Optional methods to be implemented by subclass:
      * log_move(room_id, board, to_move)
      * log_game(room_id, black_ai, white_ai, black_score, white_score, winner, by_forfeit)
    Exposed internal variables:
      * ai_list: list of AIs, supposedly in order from strongest to weakest
      * timelimit: float
      * max_games: int, maximum number of games to play at once
      * num_games: int, current number of games running
    Using add_new_game to add new games to the game queue
    """

    def __init__(self, loop, ai_list=[], timelimit=5, max_games=2):
        super().__init__(loop)

        self.ai_list = ai_list
        self.timelimit = timelimit
        self.max_games = max_games
        self.num_games = 0
    
        self.game_queue = queue.Queue()

        # populate queue with initial matchups to play
        self.populate_game_queue()
        
        # Take care of starting games ourself, because this is done way too
        # often otherwise
        while self.num_games < self.max_games and not self.game_queue.empty():
            self.play_next_game()

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

    def log_move(room_id, board, to_move):
        # Called whenever board_update intercepts a valid board
        pass

    def log_game(room_id, black_ai, white_ai, black_score, white_score, winner, by_forfeit):
        # Called whenever game_end sees that a game has ended
        pass

    def play_game(self, parsed_data, room_id):
        # send an error message back telling them they can't play
        log.warn("{} tried to play during a tournament".format(room_id))
        self.game_error({'error': "You cannot start a game during a tournament."}, room_id)
        self.game_end(dict(), room_id)

    def play_next_game(self):
        if not self.game_queue.empty():
            self.play_automatic_game(*self.game_queue.get_nowait())
            self.num_games += 1
            
            if self.num_games > self.max_games:
                log.warn("Playing more games at a time than allowed...")

    # You'll notice the number of arguments isn't specified here.
    # This is so I can add an extra argument to _play_automatic_game in a
    # below subclass. <this is fine meme>
    def play_automatic_game(self, *args):
        self.loop.call_soon_threadsafe(self._play_automatic_game, *args)

    def _play_automatic_game(self, black, white, timelimit):
        new_id = generate_id()
        # extremely low chance to block, ~~we take those~~
        while new_id in self.rooms: new_id = generate_id()
        log.info("{} playing next game: {} v {}".format(new_id, black, white))
        room = Room()
        room.id = new_id
        self.rooms[new_id] = room
        log.debug("{} starting to play".format(new_id))
        self.play_game_actual(black, white, timelimit, new_id)

        return new_id

    def game_end(self, parsed_data, room_id):
        log.debug("{} overridded game_end called".format(room_id))
        # log result
        if room_id not in self.rooms:
            log.debug("{} tried to end room, which might've already ended".format(room_id))
            return

        board = parsed_data.get('board', "")
        forfeit = parsed_data.get('forfeit', False)
        winner = parsed_data.get('winner', OUTER)
        black_score = board.count(BLACK)
        white_score = board.count(WHITE)
        black_ai = self.rooms[room_id].black_ai
        white_ai = self.rooms[room_id].white_ai

        if black_ai is None or white_ai is None:
            log.info("{} ignoring room with blank AI...".format(room_id))
            return

        super().game_end(parsed_data, room_id)
        self.num_games -= 1

        # log game
        self.log_game(room_id, black_ai, white_ai, black_score, white_score, winner, forfeit)

        # handle putting new games into queue, if necessary
        self.check_game_queue()

        while self.num_games < self.max_games and not self.game_queue.empty():
            self.play_next_game()


# Simple class to test AutomaticGameScheduler functionality
class RRTournamentScheduler(AutomaticGameScheduler):
    def populate_game_queue(self):
        for black, white in itertools.permutations(self.ai_list, 2):
            self.add_new_game(black, white)

    def check_game_queue(self):
        if not self.game_queue.empty():
            self.play_next_game()

class SetTournamentScheduler(AutomaticGameScheduler):
    # completed_callback and record_callback are called with a list of SetModel
    # object as their first argument, protected by a threading.Lock object as
    # their second argument
    def __init__(self, tournament, *args, sets=[], games_per_set=1, completed_callback=lambda *x: None, record_callback=None, **kwargs):
        self.tournament = tournament

        self.sets = sets
        self.results_lock = Lock()
        self.games = dict()
        self.games_lock = Lock()
        self.games_per_set = games_per_set
        self.currently_playing = set()

        self.completed_callback = completed_callback
        self.record_callback = record_callback if not (record_callback is None) else completed_callback
        self.completed = False

        super().__init__(*args, **kwargs)
    
    def log_move(self, room_id, board, to_move):
        # Called whenever board_update intercepts a valid board
        pass

    def log_game(self, *args): 
        # Need to have django operations be in a seperate thread
        safely_call(self.unsafe_log_game, *args)

    def unsafe_log_game(self, room_id, black_ai, white_ai, black_score, white_score, winner, by_forfeit):
        with self.games_lock:
            log.info("{} game over {} v {}".format(room_id, black_ai, white_ai))
            if room_id in self.games:
                game = self.games[room_id]
                game.black = get_player(black_ai)
                game.white = get_player(white_ai)
                game.black_score = black_score
                game.white_score = white_score
                game.winner = winner
                game.by_forfeit = by_forfeit
                game.completed = True
                
                game.save()

                # Maybe I need to do this? idk throw it out and accept the leak if
                # bad things happen
                del self.games[room_id]
            else:
                log.warn("Couldn't find existing game! Falling back to old method...")

                game = GameModel(
                    black=black_ai,
                    white=white_ai,
                    timelimit=int(self.timelimit),
                    black_score=black_score,
                    white_score=white_score,
                    winner=winner,
                    by_forfeit=by_forfeit,
                    completed=True
                )
                
                for i in self.currently_playing:
                    s = self.sets[i]
                    # No room_id -> game mapping anymore, need to search for set
                    # to add it to
                    if (s.black == black_ai and s.white == white_ai) or \
                            s.black == white_ai and s.white == black_ai:
                        add_game_to_set(s, game)

    # I wish there was a better way to do this, i.e. have GameModels correspond
    # to room_ids so we can record moves that get captured, and have us know
    # which set tried to add them at creation time.
    # But there isn't. So now we have to live with this.
    def add_new_game(self, black, white, setm, timelimit=None):
        if timelimit is None:
            self.game_queue.put_nowait((black, white, self.timelimit, setm))
        else:
            self.game_queue.put_nowait((black, white, timelimit, setm))
    
    def _play_automatic_game(self, black, white, timelimit, setm):
        room_id = super()._play_automatic_game(black.id, white.id, timelimit)
        
        with self.games_lock:
            self.games[room_id] = GameModel(
                black=black,
                white=white,
                in_set=setm,
            )
        
        safely_call(self.games[room_id].save)

    def play_next_set(self, next_set_index):
        if next_set_index in self.currently_playing:
            return

        next_set = self.sets[next_set_index]
        
        # TODO: check that `is None` works for fields set to NULL in the database
        # (because that's what these are)
        if not (next_set.black_from_set is None):
            black_prev_set = next_set.black_from_set
            winner = black_prev_set.winner
            
            if black_prev_set.winner_set.id == next_set.id:
                if winner == WHITE:
                    next_set.black = black_prev_set.white
                else:
                    # I guess this is kind of like a tiebreaker,
                    # black continues if previous set was a tie?
                    # idk, tie handling is hard
                    next_set.black = black_prev_set.black

            elif black_prev_set.loser_set.id == next_set.id:
                if winner == WHITE:
                    next_set.black = black_prev_set.black
                else:
                    next_set.black = black_prev_set.white
            else:
                log.warn("Set {}'s black previous set ({}) does not have a pointer to it".format(next_set_index, black_prev_set.num))

        if not (next_set.white_from_set is None):
            white_prev_set = next_set.white_from_set
            winner = white_prev_set.winner
            # TODO: Consider using some other method besides direct object
            # comparison to tell if two sets are the same
            if white_prev_set.winner_set.id == next_set.id:
                if winner == WHITE:
                    next_set.white = white_prev_set.white
                else:
                    next_set.white = white_prev_set.black

            elif white_prev_set.loser_set.id == next_set.id:
                if winner == WHITE:
                    next_set.white = white_prev_set.black
                else:
                    next_set.white = white_prev_set.white
            else:
                log.warn("Set {}'s white previous set ({}) does not have a pointer to it".format(next_set_index, white_prev_set.num))
        
        safely_call(next_set.save)

        for g in range(self.games_per_set):
            self.add_new_game(next_set.black, next_set.white, next_set)
            self.add_new_game(next_set.white, next_set.black, next_set)

        self.currently_playing.add(next_set_index)

    # TODO: adapt this to allow checking to see if sets are constructed
    # incorrectly, i.e. there is no way to finish a tournament because
    # the results of two games depend on each other somehow
    def populate_game_queue(self):
        all_played = True
        for i in range(len(self.sets)):
            s = self.sets[i]
            all_played = all_played and s.completed

            if s.completed or i in self.currently_playing:
                continue

            black_set_done = (s.black_from_set is None) or (s.black_from_set.completed)
            white_set_done = (s.white_from_set is None) or (s.white_from_set.completed)

            if black_set_done and white_set_done:
                self.play_next_set(i)

        if all_played:
            self.tournament_end()
        else:
            self.tournament_record()

    def check_game_queue(self):
        new_currently_playing = self.currently_playing.copy()
        for i in self.currently_playing:
            s = self.sets[i]
            log.debug("{}".format(s))
            num_games = safely_call(count_completed_games, s)
            log.debug("num_completed_games: {}".format(num_games))
            if num_games >= 2*self.games_per_set:
                s.completed = True
                safely_call(calc_set_winner, s)
                new_currently_playing.remove(i)

        self.currently_playing = new_currently_playing

        self.populate_game_queue()

    def tournament_record(self):
        log.info("Recording tournament results...")
        self.loop.call_soon_threadsafe(self.record_callback, self.sets, self.results_lock)

    def tournament_end(self):
        log.info("Tournament completed! Returning results...")
        self.loop.call_soon_threadsafe(self.completed_callback, self.sets, self.results_lock)

class SwissTournamentScheduler(SetTournamentScheduler):
    def __init__(self, *args, rounds=8, **kwargs):
        self.rounds = rounds
        self.current_round = 0
        self.num_wins = dict()

        self.last_recorded_index = 0

        super().__init__(*args, **kwargs)

    def unsafe_create_set(self, black, white):
        black_player = get_player(black)
        white_player = get_player(white)

        new_set = create_set(self.tournament, black_player, white_player)
        return new_set

    def populate_game_queue(self):
        # First, check if the current round is over
        all_played = True
        for i in range(len(self.sets)):
            s = self.sets[i]
            if not s.completed:
                all_played = False
                break

        # If it is, go to the next round
        if all_played and self.current_round < self.rounds:

            # First, calculate number of wins each AI has
            for i in range(self.last_recorded_index, len(self.sets)):
                s = self.sets[i]
                if s.winner == BLACK:
                    black_wins = self.num_wins.get(s.black.id, 0)
                    self.num_wins[s.black.id] = black_wins + 1
                elif s.winner == WHITE:
                    white_wins = self.num_wins.get(s.white.id, 0)
                    self.num_wins[s.white.id] = white_wins + 1

            self.last_recorded_index = len(self.sets)
            # Sort by number of wins
            ranking = sorted(self.ai_list, key=lambda ai: -self.num_wins.get(ai, 0))
            log.info("Swiss ranking: {}".format(ranking))
            log.info("Num wins: {}".format(self.num_wins))
            for i in range(0, len(ranking), 2):
                black = ranking[i]
                if i+1 >= len(ranking):
                    white = "random" # lowest player gets equivalent of a "bye"
                else:
                    white = ranking[i+1]

                # TODO: This doesn't record all the information I would like, i.e.
                # the set each person came from, but this should do for now
                new_set = safely_call(self.unsafe_create_set, black, white)
                self.sets.append(new_set)
            
            self.current_round += 1
        
        super().populate_game_queue()
