import random
import math

#### Othello Core
#### Adopted from Russel Norvig's original LISP solution
#### Translated to python by D.H. Connelly
#### Modifications made by P. White, TJHSST 2016-2017


EMPTY, BLACK, WHITE, OUTER = '.', '@', 'o', '?'

# To refer to neighbor squares we can add a direction to a square.
N,S,E,W = -10, 10, 1, -1
NE, SE, NW, SW = N+E, S+E, N+W, S+W
DIRECTIONS = (N,NE,E,SE,E,SW,W,NW)

class Strategy():

    def __init__(self):
        self.scores = {}

    def board_squares(self):
        """List all the valid squares on the board."""
        return [i for i in range(11, 89) if 1 <= (i % 10) <= 8]

    def get_starting_board(self):
        """Create a new board with the initial black and white positions filled."""
        board = [OUTER] * 100
        for i in self.board_squares():
            board[i] = EMPTY
        # The middle four squares should hold the initial piece positions.
        board[44], board[45] = WHITE, BLACK
        board[54], board[55] = BLACK, WHITE
        return ''.join(board)

    def get_pretty_board(self, board):
        """Get a string representation of the board."""
        rep = ''
        rep += '  %s\n' % ' '.join([str(x) for x in range(1,9)])
        for row in range(1, 9):
            begin, end = 10*row + 1, 10*row + 9
            rep += '%d %s\n' % (row, ' '.join(board[begin:end]))
        return rep

    def opponent(self, player):
        """Get player's opponent piece."""
        return BLACK if player is WHITE else WHITE

    def find_match(self, board, player, square, direction):
        """
        Find a square that forms a match with `square` for `player` in the given
        `direction`.  Returns None if no such square exists.
        """
        bracket = square + direction
        if board[bracket] == player:
            return None
        opp = self.opponent(player)
        while board[bracket] == opp:
            bracket += direction
        return None if board[bracket] in (OUTER,EMPTY) else bracket


    def is_move_valid(self, board, player, move):
        """Is this a legal move for the player?"""
        hasbracket = lambda direction: self.find_match(board, player, move, direction)
        return board[move] ==EMPTY and any(map(hasbracket,DIRECTIONS))


    def make_move(self, board, player, move):
        """Update the board to reflect the move by the specified player."""
        board = list(board)
        if not self.is_move_valid(board, player, move):
            raise self.IllegalMoveError(player, move, board)
        board[move] = player
        for d in DIRECTIONS:
            self.flip_pieces(board, player, move, d)
        return ''.join(board)


    def flip_pieces(self, board, player, move, direction):
        """Flip pieces in the given direction as a result of the move by player."""
        match = self.find_match(board, player, move, direction)
        if not match:
            return
        square = move + direction
        while square != match:
            board[square] = player
            square += direction

    def get_valid_moves(self, board, player):
        """Get a list of all legal moves for player."""
        return [sq for sq in self.board_squares() if self.is_move_valid(board, player, sq)]

    def has_any_valid_moves(self, board, player):
        """Can player make any moves?"""
        return any(self.is_move_valid(board, player, sq) for sq in self.board_squares())

    def next_player(self, board, prev_player):
        """Which player should move next?  Returns None if no legal moves exist."""
        opp = self.opponent(prev_player)
        if self.has_any_valid_moves(board, opp):
            return opp
        elif self.has_any_valid_moves(board, prev_player):
            return prev_player
        return None

    def score(self, board, player=BLACK):
        """Compute player's score (number of player's pieces minus opponent's)."""
        mine, theirs = 0, 0
        opp = self.opponent(player)
        for sq in self.board_squares():
            piece = board[sq]
            if piece == player:
                mine += 1
            elif piece == opp:
                theirs += 1
        return mine - theirs

    def game_over(self, board, player):
        """Return true is player and opponent have no valid moves"""
        return self.get_valid_moves(board, player) + \
               self.get_valid_moves(board, self.opponent(player)) == []

    ### Monitoring players

    class IllegalMoveError(Exception):
        def __init__(self, player, move, board):
            self.player = player
            self.move = move
            self.board = board

        def __str__(self):
            return '%s cannot move to square %d' % (PLAYERS[self.player], self.move)

    ################ strategies #################

    def minmax_search(self, board, player, depth):
        # determine best move for player recursively
        # it may return a move, or a search node, depending on your design
        # feel free to adjust the parameters
        pass

    def minmax_strategy(self, board, player, depth):
        # calls minmax_search
        # feel free to adjust the parameters
        # returns an integer move
        pass

    def random_strategy(self, board, player):
        return random.choice(self.get_valid_moves(board, player))

    def best_strategy(self, board, player, best_move, still_running):
        ## THIS IS the public function you must implement
        ## Run your best search in a loop and update best_move.value
        depth = 1
        while(True):
            ## doing random in a loop is pointless but it's just an example
            best_move.value = self.random_strategy(board, player)
            depth += 1

    standard_strategy = random_strategy


###############################################
# The main game-playing code
# You can probably run this without modification
################################################
import time
from multiprocessing import Value, Process
import os, signal
silent = False


#################################################
# StandardPlayer runs a single game
# it calls Strategy.standard_strategy(board, player)
#################################################
class StandardPlayer():
    def __init__(self):
        pass

    def play(self):
        ### create 2 opponent objects and one referee to play the game
        ### these could all be from separate files
        ref = Strategy()
        black = Strategy()
        white = Strategy()

        print("Playing")
        board = ref.get_starting_board()
        player = BLACK
        strategy = {BLACK: black.standard_strategy, WHITE: white.standard_strategy}
        print(ref.get_pretty_board(board))

        while player is not None:
            move = strategy[player](board, player)
            print("Player %s chooses %i" % (player, move))
            board = ref.make_move(board, player, move)
            print(ref.get_pretty_board(board))
            player = ref.next_player(board, player)

        print("Final Score %i." % ref.score(board), end=" ")
        print("%s wins" % ("Black" if ref.score(board)>0 else "White"))

#################################################
# ParallelPlayer simulated tournament play
# With parallel processes and time limits
# this may not work on Windows, because, Windows is lame
# This calls Strategy.best_strategy(board, player, best_shared, running)
##################################################
class ParallelPlayer():

    def __init__(self, time_limit = 5):
        self.black = Strategy()
        self.white = Strategy()
        self.time_limit = time_limit

    def play(self):
        ref = Strategy()
        print("play")
        board = ref.get_starting_board()
        player = BLACK

        strategy = lambda who: self.black.best_strategy if who == BLACK else self.white.best_strategy
        while player is not None:
            best_shared = Value("i", -1)
            best_shared.value = 11
            running = Value("i", 1)

            p = Process(target=strategy(player), args=(board, player, best_shared, running))
            # start the subprocess
            t1 = time.time()
            p.start()
            # run the subprocess for time_limit
            p.join(self.time_limit)
            # warn that we're about to stop and wait
            running.value = 0
            time.sleep(0.01)
            # kill the process
            p.terminate()
            time.sleep(0.01)
            # really REALLY kill the process
            if p.is_alive(): os.kill(p.pid, signal.SIGKILL)
            # see the best move it found
            move = best_shared.value
            if not silent: print("move = %i , time = %4.2f" % (move, time.time() - t1))
            if not silent:print(board, ref.get_valid_moves(board, player))
            # make the move
            board = ref.make_move(board, player, move)
            if not silent: print(ref.get_pretty_board(board))
            player = ref.next_player(board, player)

        black_score = ref.score(board, BLACK)
        if black_score > 0:
            winner = BLACK
        elif black_score < 0:
            winner = WHITE
        else:
            winner = "TIE"

        return board, ref.score(board, BLACK)

if __name__ == "__main__":
    game =  ParallelPlayer()
    game.play()
