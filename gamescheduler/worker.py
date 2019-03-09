from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging
import sys, os, io
import shlex, traceback
import multiprocessing as mp
import subprocess
import time

from .run_ai_utils import JailedRunnerCommunicator
from .othello_admin import Strategy
from .othello_core import BLACK, WHITE, EMPTY
from .utils import get_possible_strats
from .settings import OTHELLO_AI_HUMAN_PLAYER

log = logging.getLogger(__name__)

class GameRunner:
    black = None
    white = None
    timelimit = 5

    def __init__(self, room_id):
        self.possible_names = get_possible_strats()
        self.room_id = room_id

    def emit(self, data):
        # TODO: implement this somehow
        pass

    def run(self, in_q, out_q):
        """
        Main loop used to run the game in.
        Does not have multiprocess support yet.
        """
        log.debug("GameRunner started to run {} vs {} ({})".format(
            self.black,
            self.white,
            self.timelimit
        ))

        strats = dict()
        do_start_game = True

        if self.black not in self.possible_names:
            if self.black == settings.OTHELLO_AI_HUMAN_PLAYER:
                strats[BLACK] = None
            else:
                self.emit({
                    "type": "game.error",
                    "error": "{} is not a valid AI name".format(self.black)
                })
                do_start_game = False
        else:
            strat = JailedRunnerCommunicator(self.black)
            strat.start()
            strats[BLACK] = strat

        if self.white not in self.possible_names:
            if self.white == settings.OTHELLO_AI_HUMAN_PLAYER:
                strats[WHITE] = None
            else:
                self.emit({
                    "type": "game.error",
                    "error": "{} is not a valid AI name".format(self.white)
                })
                do_start_game = False
        else:
            strat = JailedRunnerCommunicator(self.white)
            strat.start()
            strats[WHITE] = strat

        log.debug("Inited strats")

        if not do_start_game:
            log.warn("Already threw error, not starting game")
            self._cleanup(strats)
            return

        core = Strategy()
        player = BLACK
        board = core.initial_board()
        names = {
            BLACK: self.black,
            WHITE: self.white,
        }

        self.emit({
            "type": "board.update",
            "board": ''.join(board),
            "tomove": BLACK,
            "black": names[BLACK],
            "white": names[WHITE],
        })
        forfeit = False

        log.debug("All initing done, time to start playing the game")

        while player is not None and not forfeit:
            player, board, forfeit = self.do_game_tick(in_q, core, board, player, strats, names)

        winner = EMPTY
        if forfeit:
            winner = core.opponent(player)
        else:
            winner = (EMPTY, BLACK, WHITE)[core.final_value(BLACK, board)]

        self.emit({
            "type": "board.update",
            "board": ''.join(board),
            "tomove": EMPTY,
            "black": names[BLACK],
            "white": names[WHITE],
        })
        self.emit({
            "type": "game.end",
            "winner": winner,
            "board": ''.join(board),
            "forfeit": forfeit,
        })

        log.debug("Game over, exiting...")
        self.cleanup(strats)


    def cleanup(self, strats):
        if getattr(strats.get(BLACK, None), "stop", False):
            strats[BLACK].stop()
            log.info("successfully stopped BLACK jailed runner")
        if getattr(strats.get(WHITE, None), "stop", False):
            strats[WHITE].stop()
            log.info("successfully stopped WHITE jailed runner")


    def do_game_tick(self, in_q, core, board, player, strats, names):
        """
        Runs one move in a game, handling all the board flips and game-ending edge cases.

        If a strat is `None`, it calls out for the user to input a move. Otherwise, it runs the strategy provided.
        """
        log.debug("Ticking game")
        strat = strats[player]
        move = -1
        errs = None
        if strat is None:
            self.emit({"type":"move.request"})
            move = in_q.get()
        else:
            move, errs = strat.get_move(board, player, self.timelimit)

        if not core.is_legal(move, player, board):
            self.emit({
                'type': "game.error",
                'error': "{}: {} is an invalid move for board {}\nMore info:\n{}".format(names[player], move, ''.join(board), errs)
            })
            return player, board, True

        board = core.make_move(move, player, board)
        player = core.next_player(board, player)
        self.emit({
            "type": "board.update",
            "board": ''.join(board),
            "tomove": player,
            "black": names[BLACK],
            "white": names[WHITE],
        })
        return player, board, False
