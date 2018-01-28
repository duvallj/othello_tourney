# Othello server
# Demian Yutin
# 12/14/2016
# extends mr. white's othello core
#
# if you're reading this code, please take a look at othello.convert_board() first

import Othello_Core as core
import random

"""
[
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
"""

SQUARE_WEIGHTS = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 27, 4, 18, 15, 15, 18, 4, 27, 0,
    0, 4, -2, 3, 8, 8, 3, -2, 4, 0,
    0, 18, 3, 9, 9, 9, 9, 3, 18, 0,
    0, 15, 8, 9, 4, 4, 9, 8, 15, 0,
    0, 15, 8, 9, 4, 4, 9, 8, 15, 0,
    0, 18, 3, 9, 9, 9, 9, 3, 18, 0,
    0, 4, -2, 3, 8, 8, 3, -2, 4, 0,
    0, 27, 4, 18, 15, 15, 18, 4, 27, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
]
SQ_W_min_value = -2  # required for things to work

SQUARES = core.OthelloCore().squares()  # instead of calling this many times per game we can just call it once and retreive the result
INF = 10 ** 10
LATE_GAME = 54  # used in heuristic

print_old = print
print = lambda *args: None

class Strategy(core.OthelloCore):
    def __init__(self):
        print("Yutin init")
        pass

    """
    squares(): returns NEW list of all valid squares on board (the interior 8 by 8 of the 100 square board)
    initial_board(): returns NEW initial board ([]*100, outer is OUTER, inner is EMPTY except for center WB/BW)
    print_board(board): returns string representing board
    """

    """ Unused functions from OthelloCore """

    def is_valid(self, move):
        return move in self.squares()

    """ Used functions from OthelloCore """

    def legal_moves(self, player, board, frontier):
        """
        player is a boolean (True iff black)
        board is a 100-list of tuples (see convert_board for full explanation)
        frontier is a list of tiles which are adjacent to non-empty tiles
        """
        result = []
        for s in frontier:
            if self.is_legal(s, player, board):
                result.append(s)
        return result

    def any_legal_move(self, player, board, frontier):
        """
        same as above
        """
        for s in frontier:
            if self.is_legal(s, player, board):
                return True
        return False

    def is_legal(self, move, player, board):  # only called for tiles in the frontier
        """
        move is an integer between 11 and 88
        player is a boolean
        board is a 100-list of tuples
        """
        for d in core.DIRECTIONS:
            if self.find_bracket(move, player, board, d):
                return True
        return False

    def find_bracket(self, square, player, board, direction):
        """
        returns True if there is a there is an unbroken string of opponent pieces
        between this tile and one of your tiles in the given direction, and False otherwise.
        
        player is a boolean
        board is a 100-list of tuples
        direction is an integer
        """
        next_square = square + direction
        if board[next_square] != (not player, True):  # can't move on a square not adjacent to opponent
            return False
        while True:
            next_square += direction
            if board[next_square][1] == False:  # empty or outer squares break the bracket
                return False
            if board[next_square][0] == player:  # a tile belonging to this player completes the bracket
                return True

    """ Functions used for runtime optimization """

    def convert_player(self, char_player):
        # in several places in my code, it is more efficient to store the player as a boolean than a character or tuple.
        return char_player == core.BLACK  # True for black, False for white

    def convert_board(self, char_board):
        # each character in board is either BLACK, WHITE, EMPTY, or OUTER.
        # in othello_core's defaults, these are @, o, ., and ?, respectively.
        # a character is stored as 8 bits, but you only need 2 bits to know what a tile contains.
        #   (because each tile may contain 1 of 4 things; 2 bits can be 00, 01, 10, or 11, i.e. 1 of 4 things)
        # using two booleans stored in a tuple in place of a character is a surprisingly effective optimization,
        # which reduced runtime by about 43%.
        #   i even did a careful statistical analysis to prove to myself that this difference was significant.
        #
        # the first boolean determines if the piece on a tile is black.
        # the second boolean determines if there is a piece on the tile.
        #   if there isn't, the first boolean determines if it's out of bounds.
        conversion = {core.BLACK: (True, True), core.WHITE: (False, True),
                      core.EMPTY: (False, False), core.OUTER: (True, False)}
        tuple_board = []
        for char in char_board:
            tuple_board.append(conversion[char])

        info = self.analyze_board(tuple_board)  # see below!
        return tuple_board, info[0], info[1]

    def analyze_board(self, board):
        # to speed up heuristic evaluation and legal moves generation, certain information about a board is kept updated as the board changes.
        # this speeds things up by eliminating the need for frequent re-counting of information that changes predictably.
        # this includes things like:
        #   the number of tiles on the board 
        #   the number of black tiles on the board
        #   weighted tile score (total)
        #   weighted tile score for black
        #   a list of frontier tiles, defined as an empty tile that is adjacent to a non-empty tile
        #       speeds up the generation of legal moves significantly, because all legal moves must be frontier tiles
        #           i.e. reduces the number of squares you have to check
        # all these values are updated by the make_move method.
        # after implementing this in combination with convert_board, i got an additional 48% decrease in runtime.
        #   a threefold average speed increase overall (after alpha-beta)
        num_tiles = 0
        num_black = 0
        weighted_total = 0
        weighted_black = 0
        frontier = []
        for s in SQUARES:
            if board[s][1]:  # if there is a piece here
                num_tiles += 1
                weighted_total += SQUARE_WEIGHTS[s]
                if board[s][0]:  # if it's black
                    num_black += 1
                    weighted_black += SQUARE_WEIGHTS[s]
            else:  # if empty
                for d in core.DIRECTIONS:  # checks for adjacent tiles
                    if board[s + d][1]:
                        frontier.append(s)
                        break
        return frontier, (num_tiles, num_black, weighted_total, weighted_black)

    def deconvert(self, tuple_board):
        """
        does the reverse of convert_board (used by client compatibility functions)
        """
        conversion = {(True, True): core.BLACK, (False, True): core.WHITE,
                      (False, False): core.EMPTY, (True, False): core.OUTER}
        char_board = []
        for tup in tuple_board:
            char_board.append(conversion[tup])
        return char_board

    def make_move_internal(self, move, player, board, frontier, stats):
        """
        returns a new board and updated frontier and stats
        updates board-related information
        seperate from make_move because make_move is used by the client with a different board format
        """
        new_board = board.copy()
        new_board[move] = (player, True)
        num_tiles = stats[0] + 1
        num_black = stats[1] + player  # True and False are 1 and 0
        weighted_total = stats[2] + SQUARE_WEIGHTS[move] - SQ_W_min_value
        weighted_black = stats[3] + player * (SQUARE_WEIGHTS[move] - SQ_W_min_value)

        new_frontier = frontier.copy()
        new_frontier.remove(move)
        for d in core.DIRECTIONS:  # add any empty non-OUTER tiles adjacent to this move to the frontier, unless they're already in the frontier
            if new_board[move + d] == (False, False) and move + d not in new_frontier:
                new_frontier.append(move + d)
            # make flips
            num_black, weighted_black = self.make_flips(move, d, player, new_board, num_black,
                                                        weighted_black)  # new_board is updated within make_flips

        return new_board, new_frontier, (num_tiles, num_black, weighted_total, weighted_black)

    def make_flips(self, move, direction, player, board, num_black=0,
                   weighted_black=0):  # used by both versions of make_move
        """
        modifies board and returns updated values for num_black and weighted_black
        """
        if self.find_bracket(move, player, board, direction):
            next_square = move + direction
            while board[next_square][0] != player:
                board[next_square] = (player, True)
                num_black += (player * 2 - 1)  # +1 if player is black, -1 if player is white
                weighted_black += (player * 2 - 1) * (SQUARE_WEIGHTS[next_square] - SQ_W_min_value)
                next_square += direction
        return num_black, weighted_black

    """ Functions that are called by the client, which uses character-based board and player format """

    def make_move(self, move, player, board):  # updates board, instead of returning updated board
        """
        because the client calls this function using character-based format,
        it can't be the same function as the one used by my server.
        because it is only called once per turn, it is unoptimized.
        """
        new_board, frontier, stats = self.convert_board(board)
        bool_player = self.convert_player(player)
        new_board[move] = (bool_player, True)
        for d in core.DIRECTIONS:
            self.make_flips(move, d, bool_player, new_board)
        result = self.deconvert(new_board)
        for i in range(100):
            board[i] = result[i]

    def next_player(self, ch_board, prev_player):
        board, frontier, trash = self.convert_board(ch_board)
        player_bool = self.convert_player(prev_player)
        if self.any_legal_move(not player_bool, board, frontier):
            return {core.BLACK: core.WHITE, core.WHITE: core.BLACK}[prev_player]
        if self.any_legal_move(player_bool, board, frontier):
            return prev_player
        return None

    def score(self, player, board):
        count = 0
        for s in SQUARES:
            if board[s] == player:
                count += 1
            if board[s] == self.opponent(player):
                count += -1
        return count

    def opponent(self, player):
        return {core.BLACK: core.WHITE, core.WHITE: core.BLACK}[player]

    def score_comparison(self, board):
        return core.PLAYERS[core.BLACK] + ": " + str(self.score(core.BLACK, board)) + "\n" + core.PLAYERS[
            core.WHITE] + ": " + str(self.score(core.WHITE, board))

    def winner(self, board):
        B = self.score(core.BLACK, board)
        W = self.score(core.WHITE, board)
        if B > W:
            return core.BLACK
        if W > B:
            return core.WHITE
        else:
            return "TIE"

    """ Strategies """

    def str_random(self, player, board):
        conv_board, frontier, trash = self.convert_board(board)  # random doesn't need board stats
        return random.choice(self.legal_moves(self.convert_player(player), conv_board, frontier))

    """
    def str_deterministic(self, player, board):
        conv_board = self.convert_board(board)
        a = self.legal_moves(self.convert_player(player), conv_board)
        L = len(a)
        i = a[L//2]%L
        return a[i]
    
    def str_human(self, player, board):
        choice = int(input("Enter a move: "))
        return choice
    """

    def str_minimax_100(self, max_depth):
        def strategy(player, board):
            conv_board, frontier, stats = self.convert_board(board)
            conv_player = self.convert_player(player)
            return self.minimax(conv_player, conv_board, frontier, stats, max_depth, 0, -INF, INF, self.eval_best)

        return strategy

    def best_strategy(self, board, player, best_move, still_running):
        """
        :param board: a length 100 list representing the board state
        :param player: WHITE or BLACK
        :param best_move: shared multiptocessing.Value containing an int of
                the current best move
        :param still_running: shared multiprocessing.Value containing an int
                that is 0 iff the parent process intends to kill this process
        :return: best move as an int in [11,88] or possibly 0 for 'unknown'
        """
        conv_board, frontier, stats = self.convert_board(board)
        conv_player = self.convert_player(player)
        best_move.value = self.minimax(conv_player, conv_board, frontier, stats, 1, 0, -INF, INF,
                                       self.eval_best)  # ensures that SOME move can be returned
        print("nominal value: ", best_move.value)
        # iterative deepening alpha-beta minimax DFS
        num_moves_remaining = 64 - stats[
            0]  # note that this assumes the game always plays out to 64 moves, which is a fair assumption to make when both players are at least somewhat smart
        max_depth = min(5,
                        num_moves_remaining)  # 5 is a reasonable initial depth but depth shouldn't exceed num_moves_remaining
        while still_running.value > 0 and max_depth <= num_moves_remaining:  # this loop would usually be killed from the client unless the end of the game was near
            best_move.value = self.minimax(conv_player, conv_board, frontier, stats, max_depth, 0, -INF, INF,
                                           self.eval_best)
            print("Current best: ", best_move.value)
            max_depth += 1  # best_move is not updated WHILE searching through the tree, but only AFTER the tree has been searched to a certain depth. whether doing this a different way would actually be an improvement is unclear.
        return best_move
        # return self.alphabeta(conv_player, conv_board, frontier, stats, best_move)# still_running is completely disregarded; the search runs until it runs out of time

    """ Heuristics / evaluation functions """

    def eval_best(self, board, frontier, stats):  # considers several heuristics and weighs them
        simple_value = stats[1] / stats[0] * 2 - 1
        weight_value = stats[3] / stats[2] * 2 - 1

        B_mobility = 0
        W_mobility = 0
        for s in frontier:  # only check frontier tiles
            mob = self.mob_helper(s, board)  # significant speed increase
            B_mobility += mob[0]
            W_mobility += mob[1]
        if (B_mobility + W_mobility) == 0:  # no moves left for either player; game is over, heuristics don't matter
            black_ratio = stats[1] / stats[0]
            if black_ratio > 0.5:  # black won
                return INF
            if black_ratio < 0.5:  # white won
                return -INF
            else:
                return 0
        mobility_value = (B_mobility - W_mobility) / (B_mobility + W_mobility)
        if B_mobility == 0:  # bonus points for not giving your opponent any moves
            mobility_value += -0.1
        if W_mobility == 0:
            mobility_value += 0.1

        corner_value = self.eval_corners(board)

        k = 0
        if stats[0] > LATE_GAME:
            k = (stats[0] - LATE_GAME) / (64 - LATE_GAME)  # k varies between 0 (not late game) and 1 (turn 64)
        M = [0 + k * 20, 50 + k * -50, 12 + k * 3,
             40 + k * -35]  # heuristic value weighting matrix that changes in the later turns of the game
        # from [0, 50, 12, 40] to [20, 0, 15, 5] (although turn 64 is always evaluated based only on simple_value)
        X = simple_value * M[0] + weight_value * M[1] + mobility_value * M[2] + corner_value * M[3]
        X /= M[0] + M[1] + M[2] + M[3]  # scale X so that it fits between -1 and 1
        """
        if random.random()*5000 < 1:
            print("a dissection")
            print(self.print_board(self.deconvert(board)))
            print("value: "+str(X))
            print("tcount/bcount: "+str(board[1])+" "+str(board[2]))
            print("weighted: "+str(board[3])+" "+str(board[4]))
            print("frontier: "+str(board[5]))
            print(str(0/0))#"""

        return X

    def mob_helper(self, square, board):
        """
        returns a tuple of 2 booleans
        first is true if black can move here
        second is true if white can move here

        this is essentially an optimization of what used to be 4 lines
        of code in my heuristic function that makes it retreive as few
        tiles from the board as possible, increasing speed by about 42%.
        """
        black = False
        white = False
        for d in core.DIRECTIONS:
            next_square = square + d
            next_tile = board[next_square]
            if next_tile[1]:  # if there is a piece here
                if not black and not next_tile[0]:  # if it's white
                    n = next_square
                    while True:
                        n += d
                        b = board[n]
                        if not b[1]:  # break if no piece
                            break
                        if b[0]:  # success if black piece
                            black = True
                            break
                if not white and next_tile[0]:  # if it's black
                    n = next_square
                    while True:
                        n += d
                        b = board[n]
                        if not b[1]:
                            break
                        if not b[0]:
                            white = True
                            break
                if black and white:
                    return (True, True)
        return (black, white)

    def eval_corners(self, board):
        b_score = 0
        w_score = 0
        for i in range(4):
            corner = [11, 18, 88, 81][i]
            adj_e1 = [12, 28, 87, 71][i]
            adj_e2 = [21, 17, 78, 81][i]
            adj_d = [22, 27, 77, 72][i]

            if board[corner][1]:  # someone controls this corner
                if board[corner][0]:  # black controls this corner
                    b_score += 15  # 15 points for controlling a corner
                    b_score += board[adj_e1][1] * [1, 4][
                        board[adj_e1][0]]  # add 4 if adjacent edge is black, 1 if it's white, 0 if it's empty
                    b_score += board[adj_e2][1] * [1, 4][board[adj_e2][0]]
                    b_score += board[adj_d][1] * [2, 5][
                        board[adj_d][0]]  # add 5 if diagonally adjacent tile is black, 2 if white, 0 if empty
                else:  # white controls this corner
                    w_score += 15
                    w_score += board[adj_e1][1] * [4, 1][board[adj_e1][0]]  # same, but in reverse, for white
                    w_score += board[adj_e2][1] * [4, 1][board[adj_e2][0]]
                    w_score += board[adj_d][1] * [5, 2][board[adj_d][0]]
            else:  # no one controls this corner
                if board[adj_e1][1]:
                    b_score += [7, 0][board[adj_e1][0]]  # increase b_score by 7 if white has the adjacent edge
                    w_score += [0, 7][
                        board[adj_e1][0]]  # (as this makes it easier for black to capture the corner in the future)
                if board[adj_e2][1]:
                    b_score += [7, 0][board[adj_e2][0]]
                    w_score += [0, 7][board[adj_e2][0]]
                if board[adj_d][1]:
                    b_score += [9, 0][
                        board[adj_d][0]]  # increase b_score by 9 if white has the diagonally adjacent tile
                    w_score += [0, 9][board[adj_d][0]]
        if (b_score + w_score) == 0:
            return 0
        return (b_score - w_score) / (b_score + w_score)

    def eval_simple(self,
                    stats):  # eval_multifaceted but without consideration of mobility or corners; a fast evaluation function
        simple_value = stats[1] / stats[0] * 2 - 1
        weight_value = stats[3] / stats[2] * 2 - 1
        k = 0
        if stats[0] > LATE_GAME:
            k = (stats[0] - LATE_GAME) / (64 - LATE_GAME)
        M = [1 + k * 15, 60 + k * -60]
        return (simple_value * M[0] + weight_value * M[1]) / (M[0] + M[1])

    """ MINIMAX WITH ALPHA-BETA """

    def minimax(self, player, board, frontier, stats, max_depth, current_d, alpha, beta, evaluation_function):
        key = {True: 1, False: -1}[player]  # allows me to condense max_dfs and min_dfs into one function

        if current_d == max_depth or self.any_legal_move(player, board, frontier) == False:  # terminal node
            return evaluation_function(board, frontier, stats)

        legal_moves = self.legal_moves(player, board, frontier)
        if len(legal_moves) == 1 and current_d == 0:
            return legal_moves[0]

        move_results = {}
        if current_d < int(1 + (
            max_depth - 3) // 4):  # pre-generate more levels for larger search trees for better alpha-beta
            for move in legal_moves:  # all top-level moves will be generated anyway
                move_result = self.make_move_internal(move, player, board, frontier, stats)
                move_results[move] = move_result
            legal_moves.sort(key=lambda x: -key * self.eval_simple(move_results[x][
                                                                       2]))  # sort top-level moves with an very quick heuristic to get the most out of alpha-beta
        else:
            random.shuffle(legal_moves)

        best_value = -key * INF
        best_move = -1
        for m in legal_moves:
            if current_d < int(1 + (max_depth - 3) // 4):
                new_board, new_frontier, new_stats = move_results[m]
            else:
                new_board, new_frontier, new_stats = self.make_move_internal(m, player, board, frontier, stats)

            new_value = self.minimax(not player, new_board, new_frontier, new_stats, max_depth, current_d + 1, alpha,
                                     beta, evaluation_function)

            if key * new_value > key * best_value:
                best_value = new_value
                best_move = m

            if key == 1:
                if best_value >= beta:
                    break  # return
                alpha = max(alpha, best_value)

            if key == -1:
                if best_value <= alpha:
                    break
                beta = min(beta, best_value)

        if current_d == 0:  # multipurpose return value
            return best_move
        else:
            return best_value


class Strategy_dumb(Strategy):  # random moves
    def __init__(self):
        pass

    def best_strategy(self, board, player, best_move, still_running):
        conv_board, frontier, trash = self.convert_board(
            board)  # trash is not needed (board stats are only used for heuristic evalutation)
        best_move.value = random.choice(self.legal_moves(self.convert_player(player), conv_board, frontier))
        return best_move
