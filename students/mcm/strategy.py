from random import shuffle


class Strategy:
    # Compatability
    # Was confused about how this whole thing was supposed to be structured, and I didn't want to go through everything to restructure
    def initial_board(self):
        c = core()
        return c.initial_board()

    def make_move(self, move, player, board):
        c = core()
        return c.make_move(move, player, board)

    def next_player(self, board, player):
        c = core()
        return c.next_player(board, player, c.SQUARES)

    def print_board(self, board):
        c = core()
        return c.print_board(board)

    def score(self, player, board):
        c = core()
        return c.score(player, board)

    class IllegalMoveError(Exception):
        def __init__(self, player, move, board):
            self.player = player
            self.move = move
            self.board = board

        def __str__(self):
            return '%s cannot move to square %d' % (PLAYERS[self.player], self.move)

    SQUARE_WEIGHTS = [
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
    ]
    DEPTHS = (2, 4, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 64, 64, 64)
    empties = None

    def best_strategy(self, board, player, best_move, still_running):
        """
        :param board: a length 100 list representing the board state
        :param player: WHITE or BLACK
        :param best_move: shared multiprocessing.Value containing an int of
                the current best move
        :param still_running: shared multiprocessing.Value containing an int
                that is 0 iff the parent process intends to kill this process
        :return: best move as an int in [11,88] or possibly 0 for 'unknown'
        """
        i = 0
        c = core()
        if self.empties == None:
            self.empties = c.initial_empty_set()
        self.empties = c.evaluate_empties(board, self.empties)
        print("Printing...")
        while still_running.value == 1:
            if i < len(self.DEPTHS):
                best_move.value = self.minimaxWrapper(board, player, self.DEPTHS[i], self.empties)
                print(self.DEPTHS[i])
                i += 1
        print("Chillin'")

    # def Random(board, player, best_move, still_running):
    #    c=core()
    #    l=c.legal_moves(player, board)
    #    shuffle(l)
    #    best_move.value=l[0]
    #    return l[0]
    # def Human(board, player):
    #    print("Make a move, "+player+"!  ")
    #    return int(input())
    # def MinimaxStrats(maxDepth):
    #    def ret(board, player):
    #        return minimaxWrapper(board, player, maxDepth)
    #    return ret
    def minimaxWrapper(self, board, player, maxDepth=15, empties=set()):
        c = core()
        return self.maxDFS(board, player, maxDepth, c, empties=empties)[1]

    def maxDFS(self, board, player, maxDepth, c, depth=0, alpha=-20000, beta=20000, empties=set()):
        if depth >= maxDepth:
            return self.value(player, board, c), 11
        v = -20000
        move = 11
        # for m in c.legal_moves(player, board):
        moves = c.legal_moves(player, board, empties)
        shuffle(moves)
        for m in moves:
            nextBoard = c.make_move(m, player, board.copy())
            nextPlayer = c.next_player(nextBoard, player, empties)
            if nextPlayer == None:
                cv = c.score(player, board) * 295
            elif nextPlayer == player:
                cv = self.value(player, board, c)
            else:
                copy = empties.copy()
                copy.remove(m)
                cv = self.minDFS(nextBoard, nextPlayer, maxDepth, c, depth + 1, alpha, beta, copy)
            if cv > v:
                v = cv
                move = m
            if v >= beta:
                return v, 11
            if v > alpha:
                alpha = v
        return v, move

    def minDFS(self, board, player, maxDepth, c, depth=0, alpha=-20000, beta=20000, empties=set()):
        if depth >= maxDepth:
            return self.value(c.opponent(player), board, c)
        v = 20000
        # for m in c.legal_moves(player, board):
        moves = c.legal_moves(player, board, empties)
        shuffle(moves)
        for m in moves:
            nextBoard = c.make_move(m, player, board.copy())
            nextPlayer = c.next_player(nextBoard, player, empties)
            if nextPlayer == None:
                cv = c.score(player, board) * -295
            elif nextPlayer == player:
                cv = -self.value(player, board, c)
            else:
                copy = empties.copy()
                copy.remove(m)
                cv = self.maxDFS(nextBoard, nextPlayer, maxDepth, c, depth + 1, alpha, beta, copy)[0]
            if cv < v:
                v = cv
            if v <= alpha:
                return v
            if v < beta:
                beta = v
        return v

    def value(self, player, board, c):
        s = 0
        opp = c.opponent(player)
        for m in range(100):
            if board[m] == player:
                s += self.SQUARE_WEIGHTS[m]
            elif board[m] == opp:
                s -= self.SQUARE_WEIGHTS[m]
        return s
        # return sum([{player:1, c.opponent(player):-1}.get(s[0],0)*s[1] for s in zip(board,SQUARE_WEIGHTS)])


from Othello_Core import BLACK, WHITE, EMPTY, DIRECTIONS, OthelloCore


class core(OthelloCore):
    SQUARES = [i for i in range(11, 89) if 1 <= (i % 10) <= 8]

    def initial_empty_set(self):
        ret = set(self.SQUARES)
        ret.remove(44)
        ret.remove(45)
        ret.remove(54)
        ret.remove(55)
        return ret

    def evaluate_empties(self, board, empties):
        q = []
        for s in empties:
            if board[s] != EMPTY:
                q.append(s)
        for s in q:
            empties.remove(s)
        return empties

    def is_valid(self, move):
        return 1 <= (move % 10) <= 8 and 10 < move < 89

    def opponent(self, player):
        # if player==WHITE:
        #    return BLACK
        # return WHITE
        return BLACK if player == WHITE else WHITE

    def find_bracket(self, square, player, board, direction, opp):
        move = square
        square += direction
        if board[square] != opp:
            return None
        while board[square] == opp:
            square += direction
        return None if board[square] != player else square

    def is_legal(self, move, player, board, opp):
        for d in DIRECTIONS:
            if self.find_bracket(move, player, board, d, opp) != None:
                return True
        return False

    def make_move(self, move, player, board):
        opp = self.opponent(player)
        for d in DIRECTIONS:
            if self.find_bracket(move, player, board, d, opp) != None:
                self.make_flips(move, player, board, d, opp)
        board[move] = player
        return board

    def make_flips(self, move, player, board, direction, opp):
        move += direction
        while board[move] == opp:
            board[move] = player
            move += direction

    def legal_moves(self, player, board, empties):
        opp = self.opponent(player)
        return [m for m in empties if board[m] == EMPTY and self.is_legal(m, player, board, opp) == True]

    def any_legal_move(self, player, board, empties):
        opp = self.opponent(player)
        for m in empties:
            if board[m] == EMPTY and self.is_legal(m, player, board, opp) == True:
                return True
        return False

    def next_player(self, board, prev_player, empties):
        if self.any_legal_move(self.opponent(prev_player), board, empties) == True:
            return self.opponent(prev_player)
        if self.any_legal_move(prev_player, board, empties) == True:
            return prev_player
        return None

    def score(self, player, board):
        return board.count(player) - board.count(self.opponent(player))
