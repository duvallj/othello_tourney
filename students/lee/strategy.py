from Othello_Core import OthelloCore as core
import random
import math

EMPTY, BLACK, WHITE, OUTER = '.', '@', 'o', '?'
PIECES = (EMPTY, BLACK, WHITE, OUTER)
PLAYERS = {BLACK: 'Black', WHITE: 'White'}

# To refer to neighbor squares we can add a direction to a square.
UP, DOWN, LEFT, RIGHT = -10, 10, -1, 1
UP_RIGHT, DOWN_RIGHT, DOWN_LEFT, UP_LEFT = -9, 11, 9, -11
DIRECTIONS = (UP, UP_RIGHT, RIGHT, DOWN_RIGHT, DOWN, DOWN_LEFT, LEFT, UP_LEFT)


class Strategy(core):
    def __init__(self):
        self.valid = self.squares()

    def squares(self):
        """List all the valid squares on the board."""
        return [i for i in range(11, 89) if 1 <= (i % 10) <= 8]

    def is_valid(self, move):
        return move in self.valid

    def opponent(self, player):
        if player == WHITE:
            return BLACK
        return WHITE

    def find_bracket(self, square, player, board, direction):
        current = square + direction
        if board[current] != self.opponent(player):
            return None
        while 8 >= (current % 10) >= 1 and 8 >= int(current / 10) >= 1:
            if board[current] == player:
                return current
            elif board[current] != self.opponent(player):
                return None
            current += direction
        return None

    def is_legal(self, move, player, board):
        for i in DIRECTIONS:
            if self.find_bracket(move, player, board, i) != None and board[move] == EMPTY:
                return True
        return False

    def make_move(self, move, player, board):
        board[move] = player
        for i in DIRECTIONS:
            self.make_flips(move, player, board, i)

    def make_flips(self, move, player, board, direction):
        other = self.opponent(player)
        cur = move + direction
        flips = []
        while board[cur] == other:
            flips.append(cur)
            cur += direction
            cur %= 100
        if board[cur] == player:
            for j in flips:
                board[j] = player

    def legal_moves(self, player, board):
        moves = []
        for i in self.valid:
            if self.is_legal(i, player, board):
                moves.append(i)
        random.shuffle(moves)
        return moves

    def any_legal_move(self, player, board):
        return len(self.legal_moves(player, board)) != 0

    def next_player(self, board, prev_player):
        if not self.any_legal_move(self.opponent(prev_player), board):
            if self.any_legal_move(prev_player, board):
                return prev_player
            return None
        return self.opponent(prev_player)

    def score(self, player, board):
        score = 0
        for i in self.valid:
            if board[i] == BLACK:
                score += 1
            elif board[i] == WHITE:
                score -= 1
        return score

    def wscore(self, player, board):
        score = 0
        w = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1000, -20, 30, 10, 10, 30, -20, 1000, 0,
            0, -20, -30, -5, 5, 5, -5, -30, -20, 0,
            0, 30, -5, 15, 3, 3, 15, -5, 30, 0,
            0, 10, 5, 3, 4, 4, 3, 5, 10, 0,
            0, 10, 5, 3, 4, 4, 3, 5, 10, 0,
            0, 30, -5, 15, 3, 3, 15, -5, 30, 0,
            0, -20, -30, -5, 5, 5, -5, -30, -20, 0,
            0, 1000, -20, 30, 10, 10, 30, -20, 1000, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ]
        for i in self.valid:
            if board[i] == BLACK:
                score += w[i]
            elif board[i] == WHITE:
                score -= w[i]
        return score / 500

    def strat(self, player, board, depth):
        moves = self.legal_moves(player, board)
        if player == BLACK:
            return self.maxi(player, board, moves, depth, float('-inf'), float('inf'))[0]
        return self.mini(player, board, moves, depth, float('-inf'), float('inf'))[0]

    def maxi(self, player, board, moves, depth, a, b):
        if len(moves) == 0:
            return -1, self.score(player, board)
        if depth == 0:
            return -1, self.wscore(player, board)
        maxval = float('-inf')
        maxmove = -1
        for i in moves:
            temp = list(board)
            self.make_move(i, player, temp)
            s = self.mini(WHITE, temp, self.legal_moves(WHITE, temp), depth - 1, a, b)[1]
            if s > maxval:
                maxval = s
                maxmove = i
            a = max(maxval, a)
            if a >= b:
                return maxmove, maxval
        return maxmove, maxval

    def mini(self, player, board, moves, depth, a, b):
        if len(moves) == 0:
            return -1, self.score(player, board)
        if depth == 0:
            return -1, self.wscore(player, board)
        minval = float('inf')
        minmove = -1
        for i in moves:
            temp = list(board)
            self.make_move(i, player, temp)
            s = self.maxi(BLACK, temp, self.legal_moves(BLACK, temp), depth - 1, a, b)[1]
            if s < minval:
                minval = s
                minmove = i
            b = min(minval, b)
            if b <= a:
                return minmove, minval
        return minmove, minval

    def best_strategy(self, board, player, best_move, still_running):
        best_move.value = self.legal_moves(player, board)[0]
        for i in range(4, 61):
            best_move.value = self.strat(player, board, i)
