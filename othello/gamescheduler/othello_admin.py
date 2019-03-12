from .othello_core import *
import random
import math

class Strategy(OthelloCore):

    def __init__(self):
        self.scores = {}

    def is_valid(self, move):
        """Is move a square on the board?"""
        return isinstance(move, int) and move in self.squares()


    def opponent(self, player):
        """Get player's opponent piece."""
        return BLACK if player is WHITE else WHITE


    def find_bracket(self, square, player, board, direction):
        """
        Find a square that forms a bracket with `square` for `player` in the given
        `direction`.  Returns None if no such square exists.
        """
        bracket = square + direction
        if board[bracket] == player:
            return None
        opp = self.opponent(player)
        while board[bracket] == opp:
            bracket += direction
        return None if board[bracket] in (OUTER, EMPTY) else bracket


    def is_legal(self, move, player, board):
        """Is this a legal move for the player?"""
        hasbracket = lambda direction: self.find_bracket(move, player, board, direction)
        return 0<=move<100 and board[move] == EMPTY and any(map(hasbracket, DIRECTIONS))


    ### Making moves

    # When the player makes a move, we need to update the board and flip all the
    # bracketed pieces.

    def make_move(self, move, player, board):
        """Update the board to reflect the move by the specified player."""
        if not self.is_legal(move, player, board):
            raise self.IllegalMoveError(player, move, board)
        board[move] = player
        for d in DIRECTIONS:
            self.make_flips(move, player, board, d)
        return board


    def make_flips(self, move, player, board, direction):
        """Flip pieces in the given direction as a result of the move by player."""
        bracket = self.find_bracket(move, player, board, direction)
        if not bracket:
            return
        square = move + direction
        while square != bracket:
            board[square] = player
            square += direction


    ### Monitoring players

    class IllegalMoveError(Exception):
        def __init__(self, player, move, board):
            self.player = player
            self.move = move
            self.board = board

        def __str__(self):
            return '%s cannot move to square %d' % (PLAYERS[self.player], self.move)


    def legal_moves(self, player, board):
        """Get a list of all legal moves for player."""
        return [sq for sq in self.squares() if self.is_legal(sq, player, board)]


    def any_legal_move(self, player, board):
        """Can player make any moves?"""
        return any(self.is_legal(sq, player, board) for sq in self.squares())


    def next_player(self,board, prev_player):
        """Which player should move next?  Returns None if no legal moves exist."""
        opp = self.opponent(prev_player)
        if self.any_legal_move(opp, board):
            return opp
        elif self.any_legal_move(prev_player, board):
            return prev_player
        return None


    def score(self,player, board):
        """Compute player's score (number of player's pieces minus opponent's)."""
        mine, theirs = 0, 0
        opp = self.opponent(player)
        for sq in self.squares():
            piece = board[sq]
            if piece == player:
                mine += 1
            elif piece == opp:
                theirs += 1
        return mine - theirs

    def game_over(self, player, board):
        return self.legal_moves(player, board) + \
            self.legal_moves(self.opponent(player), board) == []

    def no_moves(self, player, board):
        return self.legal_moves(player, board) == []

    def final_value(self, player, board):
        """The game is over--find the value of this board to player."""
        diff = self.score(player, board)
        if diff < 0:
            return -1
        elif diff > 0:
            return 1
        return diff
