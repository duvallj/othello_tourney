import Othello_Core as OthelloCore
from random import randrange
import time
from heapq import heappush, heappop, _heapify_max


class Strategy(OthelloCore.OthelloCore):
    # black is max, white is min
    nodeCount = 0
    table = dict()
    dictionary = dict()
    MAX = OthelloCore.BLACK
    MIN = OthelloCore.WHITE
    TIE = "TIE"
    legalMovesArray = [OthelloCore.UP, OthelloCore.UP_RIGHT, OthelloCore.RIGHT, OthelloCore.DOWN_RIGHT,
                       OthelloCore.DOWN, OthelloCore.DOWN_LEFT, OthelloCore.LEFT, OthelloCore.UP_LEFT]
    timeSpentInLegalMoves = 0
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
    history = []

    def opponent(self, player):
        if player == OthelloCore.BLACK:
            return OthelloCore.WHITE
        else:
            return OthelloCore.BLACK

    def is_valid(self, move):
        return 11 <= move <= 88;

    '''def print_board(self, board):
        count = 0
        for i in range(len(board)):
            if count == 9:
                count = 0
                print(board[i])
            else:
                print(board[i], end='')
                count += 1
        print("")'''

    # stableDiscs = set()
    # def stableDiscs(self, player, board):

    def find_bracket(self, square, player, board, direction):
        # not really left direction, just a kind of sample
        bracket = square + direction
        if board[bracket] == player:
            return None, False
        opp = self.opponent(player)
        while board[bracket] == opp:
            bracket += direction
        if board[bracket] == player:
            return bracket, bracket
        else:
            return None, False

    def setDirection(self, d):
        global realDirection
        realDirection = d

    def make_move(self, move, player,
                  board):  # try to do it simultaneously, copy board and if bracket is found then update the real board by setting it to the board copy
        if self.find_bracket(move, player, board, OthelloCore.UP)[1]:
            self.make_flips(move, player, board, OthelloCore.UP);
        if self.find_bracket(move, player, board, OthelloCore.UP_RIGHT)[1]:
            self.make_flips(move, player, board, OthelloCore.UP_RIGHT);
        if self.find_bracket(move, player, board, OthelloCore.RIGHT)[1]:
            self.make_flips(move, player, board, OthelloCore.RIGHT);
        if self.find_bracket(move, player, board, OthelloCore.DOWN_RIGHT)[1]:
            self.make_flips(move, player, board, OthelloCore.DOWN_RIGHT);
        if self.find_bracket(move, player, board, OthelloCore.DOWN)[1]:
            self.make_flips(move, player, board, OthelloCore.DOWN);
        if self.find_bracket(move, player, board, OthelloCore.DOWN_LEFT)[1]:
            self.make_flips(move, player, board, OthelloCore.DOWN_LEFT);
        if self.find_bracket(move, player, board, OthelloCore.LEFT)[1]:
            self.make_flips(move, player, board, OthelloCore.LEFT);
        if self.find_bracket(move, player, board, OthelloCore.UP_LEFT)[1]:
            self.make_flips(move, player, board, OthelloCore.UP_LEFT);
        board[move] = player
        return board

    def make_flips(self, move, player, board, direction):
        newmove = move + direction
        opponent = self.opponent(player)
        while board[newmove] == opponent:
            board[newmove] = player
            newmove = newmove + direction

    def findSquareInDirection(self, square, player, board, direction, legalMoves, playerSquares):
        result = self.find_bracket(square, player, board, direction)[0]
        if result is not None and result not in playerSquares:
            if self.is_valid(result):
                heappush(legalMoves, (self.SQUARE_WEIGHTS[result], result))
                playerSquares.add(result)
                return True
        return False

    def advanced_any_legal_move(self, player, board, current_d):
        return len(self.advanced_legal_moves(player, board, current_d)) > 0

    def next_player(self, board, prev_player):
        opponent = self.opponent(prev_player)
        if self.any_legal_move(opponent, board):
            return opponent
        elif self.any_legal_move(prev_player, board):
            return prev_player
        else:
            return None

    def terminal_test(self, board, player):
        whiteCount = 0
        blackCount = 0
        for i in range(len(board)):
            if board[i] == OthelloCore.WHITE:
                whiteCount += 1
            elif board[i] == OthelloCore.BLACK:
                blackCount += 1
        if blackCount > whiteCount:
            return "BLACK"
        elif whiteCount > blackCount:
            return "WHITE"
        else:
            return "TIE"

    def human(self, max_d):
        def strategy(board, player):
            move = int(input("Enter move:"))
            return move

        return strategy

    def best_strategy(self, board, player, best_move, still_running):
        best_move.value = self.random(4)(board, player)
        # print ("I am :" + player)
        self.table = dict()
        coef = 1
        if player == OthelloCore.WHITE:
            coef = -1
        partialGuess = coef * 5
        guess = (self.scoreBoard(board, player) + partialGuess, None)
        for i in range(0, 10):
            best_move.value = self.mtdf(guess, i, board, player)[1]
            # print(i)
        return best_move.value

    def alternative_strategy(self, max_d):
        def strategy(board, player):
            self.table = dict()
            coef = 1
            if player == OthelloCore.WHITE:
                coef = -1
            partialGuess = coef * 5
            guess = (self.scoreBoard(board, player) + partialGuess, None)
            for i in range(0, 8):
                guess = self.mtdf(guess, i, board, player)
                print(i)
            '''self.table = dict()
            guess = self.mtdf(guess, 2, board, player)'''
            return guess[1]
            # return self.alternative_minimax(board, player, max_d)

        return strategy

    def mtdf(self, guess, max_d, board, player):  # b is beta value in mtd(f)
        max = 1000
        min = -1000
        best = guess
        b = 0
        while min < max:
            if guess[0] == min:
                b = guess[0] + 1
            else:
                b = guess[0]
            guess = self.alternative_minimax(board, player, max_d, b - 1, b)
            if guess[1] != None:
                best = guess
            if guess[0] < b:
                max = guess[0]
            else:
                min = guess[0]
        return best

    def alternative_minimax(self, board, player, max_d, a, b):
        self.history = []
        for i in range(max_d + 15):
            self.history.append([(999, -1), (999, -1)])
        if player == OthelloCore.BLACK:
            # pickle.dump(boardToValue, fout, protocol=2)
            result = self.alternative_max_dfs(board, player, max_d, 0, a, b, None)
            return result
        if player == OthelloCore.WHITE:
            # pickle.dump(boardToValue, fout, protocol=2)
            result = self.alternative_min_dfs(board, player, max_d, 0, a, b, None)
            return result

    def scoreBoard(self, board, player):
        total = 0
        for i in range(11, 90):
            if board[i] == OthelloCore.BLACK:
                total += self.SQUARE_WEIGHTS[i]
            elif board[i] == OthelloCore.WHITE:
                total -= self.SQUARE_WEIGHTS[i]
        return total

    def random(self, max_d):
        def strategy(board, player):
            arr = self.legal_moves(player, board)
            a = arr[randrange(0, len(arr))][1]
            return a

        return strategy

    def alternative_max_dfs(self, board, player, max_d, current_d, alpha, beta, myLegalMoves):
        currentMin = self.table.get(str(board) + 'currentMin', None)
        currentMax = self.table.get(str(board) + 'currentMax', None)
        if currentMin is not None:
            if currentMin[2] >= beta and currentMin[4] >= max_d:
                # print ("here1")
                return (currentMin[0], currentMin[1], currentMin[2], currentMin[3])
            elif currentMin[4] >= max_d:
                alpha = max(alpha, currentMin[2])  # if 0 loses, try 2/3 for max, 2, min, 3
        if currentMax is not None:
            if currentMax[3] <= alpha and currentMax[4] >= max_d:
                # print ("here2")
                return (currentMax[0], currentMax[1], currentMax[2], currentMax[3])
            elif currentMax[4] >= max_d:
                beta = min(beta, currentMax[3])  # change one of these to min instead of max'''
        v = -1000  # if alpha >= beta
        move = -1
        a = alpha
        if myLegalMoves == None:
            myLegalMoves = self.advanced_legal_moves(player, board, current_d)
            # print(myLegalMoves)
        _heapify_max(myLegalMoves)
        # myLegalMoves = myLegalMoves[::-1]
        for m in myLegalMoves:
            if self.is_valid(m[1]) == False:
                continue
            boardCopyWithMove = self.make_move(m[1], player, board[:])
            opponentLegalMoves = self.advanced_legal_moves(self.opponent(player), boardCopyWithMove, current_d)
            anyLegalMovesForOpp = len(opponentLegalMoves) != 0
            if anyLegalMovesForOpp == False:
                if self.advanced_any_legal_move(player, boardCopyWithMove, current_d) == False:
                    gameresult = self.terminal_test(boardCopyWithMove, player)
                    if gameresult == "BLACK":
                        v = max(v, 999)
                        move = m[1]
                        a = max(a, v)
                    else:
                        v = max(v, -999)
                        move = m[1]
                        a = max(a, v)
                else:  # maybe it should be anyLegalMovesForOpp
                    new_value = self.scoreBoard(boardCopyWithMove, player) + 10
                    if new_value > v:
                        v = new_value
                        move = m[1]
                        a = max(a, v)
                        if v >= beta:
                            break
            elif (current_d >= max_d):
                count = self.open_squares(boardCopyWithMove)
                if count > 52 or count < 12 - max_d:
                    mindfsresult = self.alternative_min_dfs(boardCopyWithMove, self.opponent(player), max_d,
                                                            current_d + 1, a, beta,
                                                            opponentLegalMoves);
                    new_value = mindfsresult[0]
                    if new_value > v:
                        v = new_value
                        move = m[1]
                        a = max(a, v)
                        if v >= beta:  # try combining this and if on top of it for all
                            break
                else:
                    new_value = self.scoreBoard(boardCopyWithMove, player)
                    if new_value > v:
                        v = new_value
                        move = m[1]
                        a = max(a, v)
                        if v >= beta:
                            break
            else:
                mindfsresult = self.alternative_min_dfs(boardCopyWithMove, self.opponent(player), max_d, current_d + 1,
                                                        a, beta,
                                                        opponentLegalMoves);
                new_value = mindfsresult[0]
                if new_value > v:
                    v = new_value
                    move = m[1]
                    a = max(a, v)
                    if v >= beta:  # try combining this and if on top of it for all
                        break
        '''if v <= alpha:
            if str(board) + 'currentMax' in self.table:
                if self.table[str(board) + 'currentMax'][4] <= max_d:
                    self.table[str(board) + 'currentMax'] = v, move, alpha, v, max_d
            else:
                self.table[str(board) + 'currentMax'] = v, move, alpha, v, max_d
        if v > alpha and v < beta:
            print ("wrong")
            self.table[str(board) + 'currentMax'] = v, move, alpha, b, max_d
            self.table[str(board) + 'currentMin'] = v, move, alpha, b, max_d'''
        if v >= beta:
            if str(board) + 'currentMin' in self.table:
                if self.table[str(board) + 'currentMin'][4] <= max_d:
                    self.table[str(board) + 'currentMin'] = v, move, v, beta, max_d
            else:
                self.table[str(board) + 'currentMin'] = v, move, v, beta, max_d
        if move == -1:  # shouldn't happen but just in case
            print("oh no 378")
            # move = self.random(4)
        return v, move, a, beta

    def alternative_min_dfs(self, board, player, max_d, current_d, alpha, beta, myLegalMoves):
        currentMin = self.table.get(str(board) + 'currentMin', None)
        currentMax = self.table.get(str(board) + 'currentMax', None)
        if currentMax is not None:
            if currentMax[3] <= alpha and currentMax[4] >= max_d:
                # print ("here3")
                return (currentMax[0], currentMax[1], currentMax[2], currentMax[3])
            elif currentMax[4] >= max_d:
                beta = min(beta, currentMax[3])  # change one of these to min instead of max'''
        if currentMin is not None:
            if currentMin[2] >= beta and currentMin[4] >= max_d:
                # print ("here4")
                return (currentMin[0], currentMin[1], currentMin[2], currentMin[3])
            elif currentMin[4] >= max_d:
                alpha = max(alpha, currentMin[2])  # if 0 loses, try 2/3 for max, 2, min, 3
        v = 1000
        move = -1
        b = beta
        if myLegalMoves == None:
            myLegalMoves = self.advanced_legal_moves(player, board, current_d)
            # print(myLegalMoves)
        _heapify_max(myLegalMoves)
        mininloop = False
        # myLegalMoves = myLegalMoves[::-1]
        for m in myLegalMoves:
            if self.is_valid(m[1]) == False:
                continue
            mininloop = True
            boardCopyWithMove = self.make_move(m[1], player, board[:])
            opponentLegalMoves = self.advanced_legal_moves(self.opponent(player), boardCopyWithMove, current_d)
            anyLegalMovesForOpp = len(opponentLegalMoves) != 0
            if anyLegalMovesForOpp == False:
                if self.advanced_any_legal_move(player, boardCopyWithMove, current_d) == False:
                    gameresult = self.terminal_test(boardCopyWithMove, player)
                    if gameresult == "BLACK":
                        v = min(v, 999)
                        move = m[1]
                        b = min(b, v)
                    else:
                        v = min(v, -999)
                        move = m[1]
                        b = min(b, v)
                else:  # maybe it should be anyLegalMovesForOpp
                    new_value = self.scoreBoard(boardCopyWithMove, player) - 10
                    if new_value < v:
                        v = new_value
                        move = m[1]
                        b = min(b, v)
                        if v <= alpha:
                            break
            elif (current_d >= max_d):
                count = self.open_squares(boardCopyWithMove)
                if count > 52 or count < 12 - max_d:
                    maxdfsresult = self.alternative_max_dfs(boardCopyWithMove, self.opponent(player), max_d,
                                                            current_d + 1, alpha, b,
                                                            opponentLegalMoves);
                    new_value = maxdfsresult[0]
                    if new_value < v:
                        v = new_value
                        move = m[1]
                        b = min(b, v)
                        if v <= alpha:  # try combining this and if on top of it for all
                            break
                else:
                    new_value = self.scoreBoard(boardCopyWithMove, player)
                    if new_value < v:
                        v = new_value
                        move = m[1]
                        b = min(b, v)
                        if v <= alpha:
                            break
            else:
                maxdfsresult = self.alternative_max_dfs(boardCopyWithMove, self.opponent(player), max_d, current_d + 1,
                                                        alpha, b,
                                                        opponentLegalMoves);
                new_value = maxdfsresult[0]
                if new_value < v:
                    v = new_value
                    move = m[1]
                    b = min(b, v)
                    if v <= alpha:  # try combining this and if on top of it for all
                        break
        if v <= alpha:
            if str(board) + 'currentMax' in self.table:
                if self.table[str(board) + 'currentMax'][4] <= max_d:
                    self.table[str(board) + 'currentMax'] = v, move, alpha, v, max_d
            else:
                self.table[str(board) + 'currentMax'] = v, move, alpha, v, max_d
        '''if v > alpha and v < beta:
            print ("wrong")
            self.table[str(board) + 'currentMax'] = v, move, alpha, b, max_d
            self.table[str(board) + 'currentMin'] = v, move, alpha, b, max_d
        if v >= beta:
            self.table[str(board) + 'currentMin'] = v, move, v, beta, max_d #try changing it to v, beta'''
        if move == -1:  # shouldn't happen but just in case
            print("oh no 378")
            # move = self.random(4)
        return v, move, alpha, b

    newlegalmovescount = 0

    def advanced_legal_moves(self, player, board, current_d):
        if (player, str(board)) in self.dictionary:
            return self.dictionary[(player, str(board))]
        else:
            self.newlegalmovescount += 1
            # print (current_d)
            allSquares = set()
            playerSquares = set()
            legalMoves = list()
            # try the opposite
            for i in range(11, 89):
                if board[i] == OthelloCore.EMPTY:
                    allSquares.add(i)
            for square in allSquares:
                for direction in self.legalMovesArray:
                    directionresult = self.find_bracket(square, player, board, direction)[0]
                    if directionresult is not None and square not in playerSquares:
                        if self.is_valid(square):
                            legalMoves.append((self.SQUARE_WEIGHTS[square], square))
                            # heappush(legalMoves, (self.SQUARE_WEIGHTS[upleftresult], upleftresult))
                            playerSquares.add(square)
                            # continue
            self.dictionary[(player, str(board))] = legalMoves
            return legalMoves

    def combinedHeuristic(self, player, result, current_d):
        historyForDepth = self.history[current_d]
        historyHeuristicValue = 0
        if historyForDepth[0][1] == result or historyForDepth[1][1] == result:
            # print ("here")
            if player == OthelloCore.BLACK:
                historyHeuristicValue = 30 - (3 * current_d)
            else:
                historyHeuristicValue = 30 - (3 * current_d)
                # historyHeuristicValue = 0
        return self.SQUARE_WEIGHTS[result] + historyHeuristicValue

    def open_squares(self, board):
        empty = 0
        for i in range(11, 89):
            if board[i] == OthelloCore.EMPTY:
                empty += 1
        return empty

    def legal_moves(self, player, board):
        self.newlegalmovescount += 1
        # print (current_d)
        allSquares = set()
        playerSquares = set()
        legalMoves = list()
        # try the opposite
        for i in range(11, 89):
            if board[i] == OthelloCore.EMPTY:
                allSquares.add(i)
        for square in allSquares:
            for direction in self.legalMovesArray:
                directionresult = self.find_bracket(square, player, board, direction)[0];
                if directionresult is not None and square not in playerSquares:
                    if self.is_valid(square):
                        legalMoves.append((self.SQUARE_WEIGHTS[square], square))
                        # heappush(legalMoves, (self.SQUARE_WEIGHTS[upleftresult], upleftresult))
                        playerSquares.add(square)
                        # continue

        return legalMoves

    def any_legal_move(self, player, board):
        return len(self.legal_moves(player, board)) > 0

    def score(self, player, board):
        total = 0
        for i in range(11, 89):
            if board[i] == player:
                total += 1
            elif board[i] == self.opponent(player):
                total -= 1
        return total
