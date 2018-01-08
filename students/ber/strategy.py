import Othello_Core as core
import random
from pickle import load
import os, signal
import time
from multiprocessing import Process, Value
from pickle import dump


class Strategy(core.OthelloCore):
    def __init__(self):
        self.minMaxDict = {}
        reader = open('edgarmoves.pkl', 'rb')
        self.minMaxDict = load(reader)

        self.SQUARE_WEIGHTS = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 64, -8, 8, 8, 8, 8, -8, 64, 0,
            0, -8, -8, 0, 0, 0, 0, -8, -8, 0,
            0, 8, 0, 0, 0, 0, 0, 0, 8, 0,
            0, 8, 0, 0, 0, 0, 0, 0, 8, 0,
            0, 8, 0, 0, 0, 0, 0, 0, 8, 0,
            0, 8, 0, 0, 0, 0, 0, 0, 8, 0,
            0, -8, -8, 0, 0, 0, 0, -8, -8, 0,
            0, 64, -8, 8, 8, 8, 8, -8, 64, 0
        ]

    def is_valid(self, move):
        return (move < 89 and move >= 11) and (move % 10) >= 1 and (move % 10) <= 8

    def opponent(self, player):
        if player is core.BLACK:
            return core.WHITE
        else:
            return core.BLACK

    def find_bracket(self, square, player, board, direction):
        square += direction
        while (self.is_valid(square) and board[square] is self.opponent(player)):
            square += direction
            if board[square] is player:
                return square
        return None

    def is_legal(self, move, player, board):
        if self.is_valid(move) and board[move] is core.EMPTY:
            opp = self.opponent(player)
            for dir in core.DIRECTIONS:
                if self.find_bracket(move, player, board, dir) is not None:
                    return True
        return False

    ### Making moves

    # When the player makes a move, we need to update the board and flip all the
    # bracketed pieces.

    def make_move(self, move, player, board):
        board[move] = player
        for dir in core.DIRECTIONS:
            self.make_flips(move, player, board, dir)

    def make_flips(self, move, player, board, direction):
        target = self.find_bracket(move, player, board, direction)
        if (target != None):
            while move != target:
                board[move] = player
                move += direction

    def legal_moves(self, player, board):
        moves = []
        for index in range(11, 89):
            if (self.is_legal(index, player, board)):
                moves.append(index)
        random.shuffle(moves)
        return moves

    def any_legal_move(self, player, board):
        for index in range(11, 89):
            if (self.is_legal(index, player, board)):
                return True
        return False

    def next_player(self, board, prev_player):
        opp = self.opponent(prev_player)
        if self.any_legal_move(opp, board):
            return opp
        elif self.any_legal_move(prev_player, board):
            return prev_player
        return None

    def score(self, player, board):
        score = 0
        # bScore = 0
        # wScore = 0
        for index in range(11, 89):
            if (board[index] is player):
                score += 1
            elif (board[index] is self.opponent(player)):
                score -= 1
                # elif(board[index] is core.BLACK):
                #     bScore+=1
        return score

    def weightedScore(self, player, board):
        score = 0
        opp = self.opponent(player)
        for index in range(0, 100):
            if (board[index] is core.BLACK):
                score += self.SQUARE_WEIGHTS[index]
                # print(self.SQUARE_WEIGHTS[index])
            if (board[index] is core.WHITE):
                score -= self.SQUARE_WEIGHTS[index]
        # print(score)
        return score

    def random_strategy(self, board, player, best_move, still_running):
        currentMoves = self.legal_moves(player, board)
        if len(currentMoves) != 0:
            return random.choice(currentMoves)
            # print(board)
            # return self.minimax(board, player, 3, 0)
        else:
            return 0

    def best_strategy(self, board, player, best_move, still_running):
        maxDepth = 2
        while still_running.value > 0:
            move = self.minimax(board, player, maxDepth, 0)
            print("." * maxDepth, move)
            best_move.value = move
            maxDepth += 2

    def minimax(self, board, player, maxDepth, currentDepth):
        # if("".join(board),player) in self.minMaxDict:
        #    return self.minMaxDict[("".join(board),player)]
        if player == core.BLACK:
            return self.max_dfs(board, player, maxDepth, currentDepth, -10 ** 5, 10 ** 5)[1]
        elif player == core.WHITE:
            return self.min_dfs(board, player, maxDepth, currentDepth, -10 ** 5, 10 ** 5)[1]
            # self.minMaxDict[("".join(board), player)] = temp
            # fout = open('edgarmoves.pkl', 'wb')
            # dump(self.minMaxDict, fout, protocol=2)
            # fout.close()

    def max_dfs(self, board, player, maxDepth, currentDepth, alpha, beta):
        if currentDepth >= maxDepth:
            return self.weightedScore(core.BLACK, board), None

        if self.any_legal_move(player, board) is False:
            opp = self.opponent(player), None
            if self.any_legal_move(opp, board):
                return self.weightedScore(core.BLACK, board) - 10, None
            if self.weightedScore(core.BLACK, board) > self.weightedScore(core.WHITE, board):
                return 10 ** 5, None
            elif self.weightedScore(core.BLACK, board) < self.weightedScore(core.WHITE, board):
                return -10 ** 5, None
            else:
                return 0, None
        v = -10 ** 6
        move = 0
        for m in self.legal_moves(player, board):
            temp_board = list(board)
            self.make_move(m, player, temp_board)
            new_value = self.min_dfs(temp_board, self.opponent(player), maxDepth, currentDepth + 1, alpha, beta)[0]
            if new_value > v:
                v = new_value
                move = m
                alpha = max(alpha, v)
                # if currentDepth == 0 and still_running>0:
                #    best_move.value = v
            if v >= beta:
                return v, move

        return v, move

    def min_dfs(self, board, player, maxDepth, currentDepth, alpha, beta):
        if currentDepth >= maxDepth:
            return self.weightedScore(core.BLACK, board), None

        if self.any_legal_move(player, board) is False:
            opp = self.opponent(player)
            if self.any_legal_move(opp, board):
                return self.weightedScore(core.BLACK, board) + 10, None
            if self.weightedScore(core.BLACK, board) > self.weightedScore(core.WHITE, board):
                return 10 ** 5, None
            elif self.weightedScore(core.BLACK, board) < self.weightedScore(core.WHITE, board):
                return -10 ** 5, None
            else:
                return 0, None
        v = 10 ** 6
        move = 0
        for m in self.legal_moves(player, board):
            temp_board = list(board)
            self.make_move(m, player, temp_board)
            new_value = self.max_dfs(temp_board, self.opponent(player), maxDepth, currentDepth + 1, alpha, beta)[0]
            if new_value < v:
                v = new_value
                move = m
                beta = min(beta, v)
                # if currentDepth == 0 and still_running>0:
                #    best_move.value = v
            if v <= alpha:
                return v, move
        return v, move

        """
        :param board: a length 100,list representing the board state
        :param player: WHITE or BLACK
        :param best_move: shared multiptocessing.Value containing an int of
                the current best move
        :param still_running: shared multiprocessing.Value containing an int
                that is 0,iff the parent process intends to kill this process
        :return: best move as an int in [11,88] or possibly 0,for 'unknown'
        """


        # fout = open('edgarmoves.pkl', 'wb')
        # dump({}, fout, protocol=2)
        # fout.close()
