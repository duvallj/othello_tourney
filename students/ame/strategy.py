import Othello_Core as core
from random import shuffle, getrandbits
from collections import defaultdict
import os, signal
import time
import math
from array import array
from multiprocessing import Process, Value

vals = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 20, -3, 11, 8, 8, 11, -3, 20, 0, 0, -3, -7, -4, 1, 1, -4, -7, -3, 0, 0, 11, -4,
        2, 2, 2, 2, -4, 11, 0, 0, 8, 1, 2, -3, -3, 2, 1, 8, 0, 0, 8, 1, 2, -3, -3, 2, 1, 8, 0, 0, 11, -4, 2, 2, 2, 2,
        -4, 11, 0, 0, -3, -7, -4, 1, 1, -4, -7, -3, 0, 0, 20, -3, 11, 8, 8, 11, -3, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
EMPTY, BLACK, WHITE, OUTER = '.', '@', 'o', '?'
PIECES = (EMPTY, BLACK, WHITE, OUTER)
PLAYERS = {BLACK: 'Black', WHITE: 'White'}

# To refer to neighbor squares we can add a direction to a square.
UP, DOWN, LEFT, RIGHT = -10, 10, -1, 1
UP_RIGHT, DOWN_RIGHT, DOWN_LEFT, UP_LEFT = -9, 11, 9, -11
DIRECTIONS = (UP, UP_RIGHT, RIGHT, DOWN_RIGHT, DOWN, DOWN_LEFT, LEFT, UP_LEFT)


class Node():
    def __init__(self, parent=None, move=None):
        self.parent = parent
        self.w = 0.0
        self.p = 0.0
        self.children = []
        self.move = move
        self.val = 0


class Strategy(core.OthelloCore):
    def __init__(self):
        self.movedict = {}
        self.evaldict = {}
        pass

    def is_valid(self, move):
        return (1 <= (move % 10) <= 8) and (11 <= move <= 88)

    def opponent(self, player):
        """Get player's opponent piece."""
        if player == BLACK:
            return WHITE
        return BLACK

    def find_bracket(self, square, player, board, direction):
        """
        Find a square that forms a bracket with `square` for `player` in the given
        `direction`.  Returns None if no such square exists.
        Returns the index of the bracketing square if found
        """
        hasPassed = False
        curSquare = square + direction
        while self.is_valid(curSquare) and board[curSquare] != EMPTY:
            if board[curSquare] == self.opponent(player):
                hasPassed = True
                curSquare += direction
            elif board[curSquare] == player:
                if hasPassed:
                    return curSquare
                else:
                    return None
        return None

    def is_legal(self, move, player, board):
        """Is this a legal move for the player?"""
        for x in DIRECTIONS:
            if self.find_bracket(move, player, board, x) != None:
                return True
        return False

        ### Making moves

        # When the player makes a move, we need to update the board and flip all the
        # bracketed pieces.

    def make_move(self, move, player, board):
        """Update the board to reflect the move by the specified player."""
        board[move] = player
        for x in DIRECTIONS:
            self.make_flips(move, player, board, x)

    def make_new_board(self, move, player, board):
        new = array('u', board)
        self.make_move(move, player, new)
        return new

    def make_flips(self, move, player, board, direction):
        """Flip pieces in the given direction as a result of the move by player."""
        bracket = self.find_bracket(move, player, board, direction)
        if bracket != None:
            cur = move + direction
            while cur != bracket:
                board[cur] = player
                cur += direction

    def legal_moves(self, player, board):
        """Get a list of all legal moves for player, as a list of integers"""
        op = self.opponent(player)
        moves = []
        for x in self.squares():
            if board[x] == EMPTY:
                if board[x + UP] == op or board[x + DOWN] == op or board[x + LEFT] == op or board[x + RIGHT] == op or \
                                board[x + UP_RIGHT] == op or board[x + DOWN_RIGHT] == op or board[x + UP_LEFT] == op or \
                                board[x + DOWN_LEFT] == op:
                    if self.is_legal(x, player, board):
                        moves.append(x)
        return moves

    def any_legal_move(self, player, board):
        """Can player make any moves? Returns a boolean"""
        op = self.opponent(player)
        for x in self.squares():
            if board[x] == EMPTY:
                if board[x + UP] == op or board[x + DOWN] == op or board[x + LEFT] == op or board[x + RIGHT] == op or \
                                board[x + UP_RIGHT] == op or board[x + DOWN_RIGHT] == op or board[x + UP_LEFT] == op or \
                                board[x + DOWN_LEFT] == op:
                    if self.is_legal(x, player, board):
                        return True
        return False

    def next_player(self, board, prev_player):
        """Which player should move next?  Returns None if no legal moves exist."""
        if self.any_legal_move(self.opponent(prev_player), board):
            return self.opponent(prev_player)
        if self.any_legal_move(prev_player, board):
            return prev_player
        return None

    def score(self, player, board):
        """Compute player's score (number of player's pieces minus opponent's)."""
        score = 0
        op = self.opponent(player)
        for i in self.squares():
            if board[i] == player:
                score += 1
            elif board[i] == op:
                score -= 1
        return score

    def get_random_move(self, player, board):
        moves = self.legal_moves(player, board)
        shuffle(moves)
        return moves[0]

    def get_move(self, player, board):
        best_move = Value("i", 0)
        running = Value("i", 1)
        p = Process(target=self.best_strategy, args=(board, player, best_move, running))
        p.start()
        t1 = time.time()
        p.join(5)
        if p.is_alive():
            time.sleep(5)  # let it run a little longer
            running.value = 0  # tell it we're about to stop
            time.sleep(0.1)  # wait a bit
            p.terminate()  # terminate
            time.sleep(0.1)  # wait a bit

        if p.is_alive():
            print("STILL ALIVE: Force Kill")
            os.kill(p.pid, signal.SIGKILL)  # make the OS destroy it
        t2 = time.time()

        move = best_move.value  # get the final best move

        return move

    def best_strategy(self, board, player, best_move, still_running):
        arrayboard = array('u', board)
        if player == BLACK:
            for i in range(3, 63):
                move = \
                self.maxdfs(arrayboard, 0, i, -1000000000000000000000000000, 1000000000000000000000000000, False)[1]
                best_move.value = move
        else:
            for i in range(3, 63):
                move = \
                self.mindfs(arrayboard, 0, i, -1000000000000000000000000000, 1000000000000000000000000000, False)[1]
                best_move.value = move

    def bester_strategy(self, board, player, best_move, still_running):
        startNode = Node()
        num = 1
        while startNode.p < 64:
            self.mcarlo(board, self.opponent(player), startNode, player)
            num += 1
        while True:
            if still_running.value == 0 or num % 200 == 0:
                bestVal = (-1, None)
                for child in startNode.children:
                    val = child.w / child.p
                    if val > bestVal[0]:
                        bestVal = (val, child)
                print(str(bestVal[1].w) + "/" + str(bestVal[1].p) + " = " + str(bestVal[0]))
                best_move.value = bestVal[1].move
            self.mcarlo(board, self.opponent(player), startNode, player)
            num += 1

    def maxdfs(self, board, depth, maxdepth, alpha, beta, nextnone):
        num = self.boardToNum(board)
        if (num, True, maxdepth - depth) in self.movedict:
            return self.movedict[(num, True, maxdepth - depth)]
        if nextnone:
            score = self.score(BLACK, board)
            if score < 0:
                return (-1000000000 + score, None)
            if score > 0:
                return (1000000000 + score, None)
            return (0, None)
        elif depth > maxdepth:
            return (self.eval(board, num), None)
        possible = self.legal_moves(BLACK, board)
        sorted(possible, key=lambda x: -vals[x])
        # shuffle(possible)
        if depth == 0 and len(possible) == 1:
            return (0, possible[0])
        v = (-1000000000000000000000000000, None)
        for i in possible:
            new = self.make_new_board(i, BLACK, board)
            nextplayer = self.next_player(new, BLACK)
            if nextplayer != BLACK:
                x = self.mindfs(new, depth + 1, maxdepth, alpha, beta, nextplayer == None)[0], i
                if x[0] > v[0]:
                    v = x
                if v[0] > alpha:
                    alpha = v[0]
                if alpha >= beta:
                    return v
            else:
                x = self.maxdfs(new, depth + 1, maxdepth, alpha, beta, False)[0], i
                if x[0] > v[0]:
                    v = x
                if v[0] > alpha:
                    alpha = v[0]
                if alpha >= beta:
                    return v
        self.movedict[(num, True, maxdepth - depth)] = v
        return v

    def mindfs(self, board, depth, maxdepth, alpha, beta, nextnone):
        num = self.boardToNum(board)
        if (num, False, maxdepth - depth) in self.movedict:
            return self.movedict[(num, False, maxdepth - depth)]
        if nextnone:
            score = self.score(BLACK, board)
            if score < 0:
                return (-1000000000 + score, None)
            if score > 0:
                return (1000000000 + score, None)
            return (0, -1)
        elif depth > maxdepth:
            return (self.eval(board, num), None)
        possible = self.legal_moves(WHITE, board)
        sorted(possible, key=lambda x: -vals[x])
        # shuffle(possible)
        if depth == 0 and len(possible) == 1:
            return (0, possible[0])
        v = (1000000000000000000000000000, None)
        for i in possible:
            new = self.make_new_board(i, WHITE, board)
            nextplayer = self.next_player(new, WHITE)
            if nextplayer != WHITE:
                x = self.maxdfs(new, depth + 1, maxdepth, alpha, beta, nextplayer == None)[0], i
                if x[0] < v[0]:
                    v = x
                if v[0] < beta:
                    beta = v[0]
                if beta <= alpha:
                    return v
            else:
                x = self.mindfs(new, depth + 1, maxdepth, alpha, beta, False)[0], i
                if x[0] < v[0]:
                    v = x
                if v[0] < beta:
                    beta = v[0]
                if beta <= alpha:
                    return v
        self.movedict[(num, False, maxdepth - depth)] = v
        return v

    def eval(self, board, num):
        rep = num
        if rep in self.evaldict:
            return self.evaldict[rep]
        mine = 0.0
        theirs = 0.0
        sumval = 0.0
        my_outer_value = 0.0
        their_outer_value = 0.0
        for i in self.squares():
            if board[i] == BLACK:
                mine += 1
                sumval += vals[i]
                for j in DIRECTIONS:
                    if board[i + j] == EMPTY:
                        my_outer_value += 1
                        break
            elif board[i] == WHITE:
                theirs += 1
                sumval -= vals[i]
                for j in DIRECTIONS:
                    if board[i + j] == EMPTY:
                        their_outer_value += 1
                        break
        corner = 0
        if board[11] == BLACK:
            corner += 25
        elif board[11] == WHITE:
            corner -= 25
        if board[18] == BLACK:
            corner += 25
        elif board[18] == WHITE:
            corner -= 25
        if board[81] == BLACK:
            corner += 25
        elif board[81] == WHITE:
            corner -= 25
        if board[88] == BLACK:
            corner += 25
        elif board[88] == WHITE:
            corner -= 25
        mymoves = float(len(self.legal_moves(BLACK, board)))
        oppmoves = float(len(self.legal_moves(WHITE, board)))
        moves = 0
        diff = 0
        outer = 0
        if mymoves > oppmoves:
            moves = 100 * (mymoves) / (mymoves + oppmoves)
        elif oppmoves > mymoves:
            moves = -100 * (oppmoves) / (mymoves + oppmoves)
        if mine > theirs:
            diff = 100 * (mine) / (mine + theirs)
        elif theirs > mine:
            diff = -100 * (theirs) / (mine + theirs)
        if my_outer_value > their_outer_value:
            outer = -100 * (my_outer_value) / (my_outer_value + their_outer_value)
        elif my_outer_value < their_outer_value:
            outer = 100 * (their_outer_value) / (my_outer_value + their_outer_value)
        myedges, theiredges = 0.0, 0.0
        for i in range(8):
            if board[11 + i] == BLACK:
                myedges += 1
            elif board[11 + i] == WHITE:
                theiredges += 1
            if board[11 + i * 10] == BLACK:
                myedges += 1
            elif board[11 + i * 10] == WHITE:
                theiredges += 1
            if board[18 + i * 10] == BLACK:
                myedges += 1
            elif board[18 + i * 10] == WHITE:
                theiredges += 1
            if board[81 + i] == BLACK:
                myedges += 1
            elif board[81 + i] == WHITE:
                theiredges += 1
        edges = 0
        if myedges > theiredges:
            edges = 100 * (myedges) / (myedges + theiredges)
        elif myedges < theiredges:
            edges = -100 * (theiredges) / (myedges + theiredges)
        answer = sumval * 10 + corner * 700 + moves * 78.92 + diff * 10 + outer * 74.4 + edges * 50
        self.evaldict[rep] = answer
        return answer

    def boardToNum(self, board):
        boardstr = ""
        for i in self.squares():
            if board[i] == ".":
                boardstr = boardstr + "0"
            elif board[i] == "@":
                boardstr = boardstr + "1"
            elif board[i] == "o":
                boardstr = boardstr + "2"
        return int(boardstr, 3)

    def mcarlo(self, board, player, currNode, origplayer):
        nextplayer = self.next_player(board, player)
        if nextplayer == None:
            score = self.score(origplayer, board)
            winner = score > 0 or score == 0 and bool(getrandbits(1))
            self.backprop(currNode, winner)
            return
        lenchilds = len(currNode.children)
        if lenchilds == 0:
            currNode.children = [Node(currNode, x) for x in self.legal_moves(nextplayer, board)]
            lenchilds = len(currNode.children)
        shuffle(currNode.children)
        bestChild = None
        bestVal = -1000000000000000000000
        for child in currNode.children:
            if child.p == 0:
                bestChild = child
                break
            if child.parent.p >= lenchilds:
                val = child.val
                if val > bestVal:
                    bestChild = child
                    bestVal = val
        self.mcarlo(self.make_new_board(bestChild.move, nextplayer, board), nextplayer, bestChild, origplayer)

    def reeval(self, node):
        C = 0.5
        node.val = node.w / node.p + C * math.sqrt(2 * math.log(node.parent.p) / node.p)

    def backprop(self, currNode, win):
        node = currNode
        while node != None:
            node.p += 1
            if win:
                node.w += 1
            node = node.parent
        node = currNode
        while node.parent != None:
            self.reeval(node)
            node = node.parent
