# This is a sample client for testing a parallel implementation of Othello
# it uses one object (subclass of Othello_Core) to make plays and get moves
#
#
# Created by: Patrick White
# Date: Jan 2017
# TJHSST
#


# change the following one line to your strategy file name
import strategy as ai
import Othello_Core as core  ## to access constants directly

## in my client, I will import MY core file to run the game, but for testing you can just
## use your own

import time
from multiprocessing import Process, Value
import os, signal

ai1 = ai.Strategy()  ### your strategy object
ai2 = ai1  ## make this different to play 2 different strategy files


def tournament_player(black_choice, white_choice, black_name="Black", white_name="White", time_limit=5):
    """ runs a tournament of an even number of games, alternating black/white with each strategy
        and returns the results """
    ai1_wins = 0
    rounds = 5
    for i in range(2 * rounds):
        try:
            (black, white) = black_choice, white_choice
            board, score = play(black, white, black_name, white_name, time_limit)
            ai1_wins += 1 if score > 0 else 0
            print('%s wins!' % ('AI1' if score > 0 else 'AI2'))

            (black, white) = white_choice, black_choice
            board, score = play(black, white, black_name, white_name, time_limit)
            ai1_wins += 1 if score < 0 else 0
            print('%s wins!' % ('AI2' if score > 0 else 'AI1'))

        except ai1.IllegalMoveError as e:
            print(e)
            return
    print("strategy A won", ai1_wins, "out of", 2 * rounds)
    return ai1_wins


def play(black_strategy, white_strategy, black_name, white_name, time_limit=60):
    """Play a game of Othello and return the final board and score."""
    board = ai1.initial_board()
    player = core.BLACK

    strategy = lambda who: black_strategy if who == core.BLACK else white_strategy
    while player is not None:
        start_time = time.time()

        best_shared = Value("i", -1)
        best_shared.value = 11
        running = Value("i", 1)
        p = Process(target=strategy(player), args=(board, player, best_shared, running))
        p.start()
        t1 = time.time()
        p.join(time_limit)
        running.value = 0
        time.sleep(0.01)
        p.terminate()
        time.sleep(0.01)
        if p.is_alive(): os.kill(p.pid, signal.SIGKILL)

        move = best_shared.value
        print("move = ", move)
        ai1.make_move(move, player, board)
        print(ai1.print_board(board))
        player = ai1.next_player(board, player)

    black_score = ai1.score(core.BLACK, board)
    if black_score > 0:
        winner = black_name
    elif black_score < 0:
        winner = white_name
    else:
        winner = "TIE"

    return board, ai1.score(core.BLACK, board)


if __name__ == "__main__":
    tournament_player(ai1.best_strategy, ai2.best_strategy, "black", "white", 2)
