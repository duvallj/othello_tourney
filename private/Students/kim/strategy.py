# weighted eval (?) corners are best, next to corners are bad, etc
# if no valid move, skip player
# use core.[thing] to access things in core

import random
import Othello_Core as core

squares = tuple(i for i in range(11, 89) if 1 <= (i % 10) <= 8)
SQUARE_WEIGHTS = (
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 120, -20, 20, 5, 5, 20, -20, 120, 0,
    0, -20, -40, -5, -5, -5, -5, -40, -20, 0,
    0, 20, -5, 15, 3, 3, 15, -5, 20, 0,
    0, 5, -5, 3, 3, 3, 3, -5, 5, 0,
    0, 5, -5, 3, 3, 3, 3, -5, 5, 0,
    0, 20, -5, 15, 3, 3, 15, -5, 20, 0,
    0, -20, -40, -5, -5, -5, -5, -40, -20, 0,
    0, 120, -20, 20, 5, 5, 20, -20, 120, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
)


class Strategy(core.OthelloCore):
    def __init__(self):
        pass

    def squares(self):
        return list(squares)

    def is_valid(self, move):
        """Is move a square on the board?"""
        return 11 <= move <= 88 and 1 <= move % 10 <= 8

    def opponent(self, player):
        """Get player's opponent piece."""
        if player is core.BLACK:
            return core.WHITE
        else:
            return core.BLACK

    def find_bracket(self, square, player, board, direction):
        """
        Find a square that forms a bracket with `square` for `player` in the given
        `direction`.  Returns None if no such square exists.
        Returns the index of the bracketing square if found
        """
        # if it finds another piece of the same color it'll return its indes, otherwise returns nothing
        # find_bracket will be called for all 8 directions
        current = square + direction
        opponent = self.opponent(player)
        if board[current] == player or current not in squares:
            return None
        while board[current] is opponent:
            current = current + direction
        return current if board[current] == player else None

    def is_legal(self, move, player, board):
        """Is this a legal move for the player?"""
        if board[move] != core.EMPTY:
            return False
        for direction in core.DIRECTIONS:
            if self.find_bracket(move, player, board, direction) is not None:
                return True
        return False

    ### Making moves

    # When the player makes a move, we need to update the board and flip all the
    # bracketed pieces.

    def make_move(self, move, player, board):
        """Update the board to reflect the move by the specified player."""
        board[move] = player
        for d in core.DIRECTIONS:
            self.make_flips(move, player, board, d)
        return board

    def make_flips(self, move, player, board, direction):
        """Flip pieces in the given direction as a result of the move by player."""
        end = self.find_bracket(move, player, board, direction)
        if end is None:
            return board
        i = move
        while i != end:
            board[i] = player
            i += direction
        return board

    def legal_moves(self, player, board):
        """Get a list of all legal moves for player, as a list of integers"""
        return [m for m in squares if self.is_legal(m, player, board)]

    def any_legal_move(self, player, board):
        """Can player make any moves? Returns a boolean"""
        return any(self.is_legal(m, player, board) for m in squares)

    def next_player(self, board, prev_player):
        """Which player should move next?  Returns None if no legal moves exist."""
        new_player = self.opponent(prev_player)
        if self.any_legal_move(new_player, board):
            return new_player
        elif self.any_legal_move(prev_player, board):
            return prev_player
        else:
            return None

    def score(self, player, board):
        """Compute player's score (number of player's pieces minus opponent's)."""
        p = 0
        o = 0
        opponent = self.opponent(player)
        for sq in board:
            if sq == player:
                p += 1
            elif sq == opponent:
                o += 1
        return p - o

        # STRATEGIES (all take a player and board)

    # like corners can have a 100 val and the ones surrounding can be -40 then the next layer 20 ? and like 3 near the center
    # then valuing each possible move w the weighted scores
    def human(self, board, player):
        move = input("move: ")
        b = list(board)
        while b[move] is not '.':
            move = input("move: ")
        return move

    def random_strategy(self, board, player, best_move=0, still_running=0):
        move = random.choice(self.legal_moves(player, board))
        return move

    def best_strategy(self, board, player, best_move, still_running):
        '''
        needs to be able to have a best move prepared bc 10 sec limit
        :param board:  length 100 list representing the board state
        :param player: WHITE or BLACK
        :param best_move: shared multiprocessing.Value containing an int of the curent best move
        :param still_running: shared multiprocessing.Value containing an int that is 0 iff the parent process intends to kill this process
        :return: best move as an int [11,88] or possibly 0 for 'unknown'
        whever u come up w a best current--> best_shared.value = move
        run alpha-beta 3, store best move, run a-b 4, stre again, etcetc until process is killed

        best_move = self.alpha_beta_search(board,player)[1]
        print best_move
        return best_move
        '''
        ab = 3
        while still_running.value > 0 and best_move.value < 1000:
            best_move.value = self.alpha_beta(board, player, ab)[1]
            ab += 1
        return best_move.value

    def alpha_beta(self, board, player, remaining_depth, a=-float("inf"), b=float("inf")):
        m = self.max_value(board, player, remaining_depth, a, b)
        return m

    def max_value(self, board, player, remainingdepth, a, b):
        '''if self.terminal_test(board, player):
            return
        v = -float("inf")
        legalmoves = self.legal_moves(player, board)
        for l in legalmoves:
            v = max(v, min_value)
        return v'''
        if remainingdepth <= 0:
            return (self.eval(board, player), None)
        remainingdepth -= 1
        legalmoves = self.legal_moves(player, board)
        if not legalmoves:
            return (self.eval(board, player), None)
        random.shuffle(legalmoves)  # ?? or sort legalmoves by weights
        opponent = self.opponent(player)
        bestmove = None
        bestval = -float("inf")
        for m in legalmoves:
            nextboard = self.make_move(m, player, board[:])
            nextplayer = self.next_player(nextboard, player)
            v = None
            if nextplayer == player:
                v = self.max_value(nextboard, player, remainingdepth - 1, a, b)[0]
            elif nextplayer == opponent:
                v = -self.min_value(nextboard, opponent, remainingdepth, -b, -a)[0]
            else:  # neither has legal moves; game is finished
                v = self.eval(nextboard, player)
            if v > bestval:
                bestmove = m
                bestval = v
            if v > a:
                a = v
            if a >= b:
                break
        return (bestval, bestmove)

    def min_value(self, board, player, remainingdepth, a, b):  # max for the opponent player
        if remainingdepth <= 0:
            return (self.eval(board, player), None)
        remainingdepth -= 1
        legalmoves = self.legal_moves(player, board)
        if not legalmoves:
            return (self.eval(board, player), None)
        # random.shuffle(legalmoves) #?? sort legalmoves by weights
        opponent = self.opponent(player)
        bestmove = None
        bestval = -float("inf")
        for m in legalmoves:
            nextboard = self.make_move(m, player, board[:])
            nextplayer = self.next_player(nextboard, player)
            v = None
            if nextplayer == player:
                v = self.min_value(nextboard, player, remainingdepth - 1, a, b)[0]
            elif nextplayer == opponent:
                v = -self.max_value(nextboard, opponent, remainingdepth, -b, -a)[0]
            else:  # neither has legal moves; game is finished
                v = self.eval(nextboard, player)
            if v > bestval:
                bestmove = m
                bestval = v
            if v > a:
                a = v
            if a >= b:
                break
        return (bestval, bestmove)

    def eval(self, board, player):
        if self.terminal_test(board, player):
            score = self.score(player, board)
            return score + (1 << 28) * ((score > 0) - (score < 0))
        opponent = self.opponent(player)
        x = 0
        for i in squares:
            if board[i] == player:
                x += SQUARE_WEIGHTS[i]
            elif board[i] == opponent:
                x -= SQUARE_WEIGHTS[i]
        # x += len(self.legal_moves(player, board)) * 15
        return x

    def terminal_test(self, board, player):
        return self.next_player(board, player) is None
