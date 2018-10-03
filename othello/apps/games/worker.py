from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging
import sys, os, io
import shlex, traceback
import multiprocessing as mp
import subprocess
import time

from .run_ai_utils import JailedRunnerCommunicator, RawRunner
from .othello_admin import Strategy
from .othello_core import BLACK, WHITE, EMPTY

log = logging.getLogger(__name__)

class GameRunner:
    black = None
    white = None
    timelimit = 5

    def __init__(self, room_id):
        student_folder = settings.MEDIA_ROOT
        folders = os.listdir(student_folder)
        log.debug('Listed student folders successfully')
        self.possible_names =  {x for x in folders if \
            x != '__pycache__' and \
            os.path.isdir(os.path.join(student_folder, x))
        }
        self.emit_func = None
        self.room_id = room_id
    
    def emit(self, data):
        log.debug("GameRunner emitting {}".format(data))
        if self.emit_func is None:
            log.warn("GameRunner not ready to emit")
        else:
            self.emit_func(
                self.room_id,
                data,
            )
    
    def run(self, comm_queue):
        """
        Main loop used to run the game in.
        Does not have multiprocess support yet.
        """
        log.debug("GameRunner started to run {} vs {} ({})".format(
            self.black,
            self.white,
            self.timelimit
        ))
        
        self.emit_func = async_to_sync(get_channel_layer().group_send)
        
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
        elif self.black == settings.OTHELLO_AI_UNLIMITED_PLAYER:
            log.info("Using Unlimited Runner")
            self.emit({
                "type": "game.error",
                "error": "Using Unlimited Runner"
            })
            strat = RawRunner(self.black)
            strats[BLACK] = strat
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
            player, forfeit, board = self.do_game_tick(comm_queue, core, board, player, strats, names)
            
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
            "forfeit": forfeit,
        })

        log.debug("Game over, exiting...")
        
    def do_game_tick(self, comm_queue, core, board, player, strats, names):
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
            move = comm_queue.get()
        else:
            move, errs = strat.get_move(board, player, self.timelimit)
            
        if not core.is_legal(move, player, board):
            self.emit({
                'type': "game.error",
                'error': "{}: {} is an invalid move for board {}\nMore info:\n{}".format(names[player], move, ''.join(board), errs)
            })
            forfeit = True
            return player, forfeit, board
            
        board = core.make_move(move, player, board)
        player = core.next_player(board, player)
        self.emit({
            "type": "board.update", 
            "board": ''.join(board),
            "tomove": player,
            "black": names[BLACK],
            "white": names[WHITE],
        })
        return player, False, board
        
