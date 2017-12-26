import pickle
import time
#from math import inf
inf = float('inf')
from multiprocessing import Process, Value

import Othello_Core as oc
import my_core

sq = oc.OthelloCore().squares()

def load_matrix(filename):
    try:
        file = open(filename, 'rb')
        mtrx = pickle.load(file)
        file.close()
        return mtrx
    except (FileNotFoundError, EOFError):
        return dict()


def write_matrix(matrix, filename):
    file = open(filename, 'wb')
    pickle.dump(matrix, file)
    file.close()


# tDict = loadMatrix('C:/Users/Me/Documents/AI/othello/lookupdict.pkl')
class Strategy(my_core.MyCore):
    def __init__(self):
        super().__init__()
        self.tMatrix = load_matrix('./nmatrix.pkl')
        self.players = oc.BLACK+oc.WHITE

    def best_strategy(self, board, player, move, flag):
        tDict = {}
        spots_left = set(x for x in sq if board[x] == oc.EMPTY)
        startnode = [0, board, player, spots_left, [], None, find_all_brackets(board, player, spots_left, self), -1, -1, player+''.join(board)]
        # Node structure:
        # * 0 = score
        # * 1 = board
        # * 2 = player
        # * 3 = spots left
        # * 4 = children nodes
        # * 5 = parent node
        # * 6 = brackets (only legal moves)
        # * 7 = prev move
        # * 8 = best move
        # * 9 = condensed board w/ player (for lookups)
        move.value = abprune(startnode, self, 0, 2, self.tMatrix, -inf, inf, player, tDict)[1]  #
        print(move.value)
        startnode = [0, board, player, spots_left, [], None, startnode[6], -1, -1, player+''.join(board)]  #
        move.value = abprune(startnode, self, 0, 4, self.tMatrix, -inf, inf, player, tDict)[1]  #
        print(move.value)

        d = 6
        while d<130:

            startnode = [0, board, player, spots_left, [], None, startnode[6], -1, -1, player+''.join(board)]  #
            move.value = abprune(startnode, self, 0, d, self.tMatrix, -inf, inf, player, tDict)[1]
            print(move.value,d)
            d += 1


def abprune(node, core, depth, maxdepth, matrix, alpha, beta, oplayer, lookupdict):
    if depth > maxdepth or len(node[3]) == 0:
        #return node[0], node[7]
        return score(node[1], oplayer, core, matrix, len(node[6])), node[7]

    if node[2] == oplayer:
        v = -inf
        best = None
        gen_all_good_children(node, core, matrix, oplayer, lookupdict)
        for child in node[4]:
            newv, a = abprune(child, core, depth + 1, maxdepth, matrix, alpha, beta, oplayer, lookupdict)

            if newv > v:
                v = newv
                best = child
            if v >= beta:
                return v, best[7]

            if v > alpha:
                alpha = v
    else:
        v = inf
        best = None
        gen_all_good_children(node, core, matrix, oplayer, lookupdict)
        for child in node[4]:
            newv, a = abprune(child, core, depth + 1, maxdepth, matrix, alpha, beta, oplayer, lookupdict)

            if newv < v:
                v = newv
                best = child
            if v <= alpha:
                return v, best[7]

            if v < beta:
                beta = v
    return v, best[7]


def gen_all_good_children(node, core, matrix, oplayer, lookupdict):  #
    # We can't generate children if it is an end-case
    if len(node[3]) == 0:
        return

    elif node[9] in lookupdict:
        node[4] = lookupdict[node[9]][4]
    else:

        for spot in node[6]:
            nboard = node[1].copy()
            for direction in node[6][spot]:
                for flipspot in range(spot, node[6][spot][direction], direction):
                    nboard[flipspot] = node[2]

            nspots_left = node[3] - {spot}
            oppo = core.opponent(node[2])
            brackets = find_all_brackets(nboard, oppo, nspots_left, core)

            nscore = 0 #score(nboard, oplayer, core, matrix, len(brackets))

            # If we can't make a move
            if len(brackets) == 0:

                # Try the original player again
                oppo = node[2]
                brackets = find_all_brackets(nboard, oppo, nspots_left, core)

                if len(brackets) == 0:
                    # If they still can't make a move, score the board
                    mcount = nboard.count(oplayer)
                    ocount = nboard.count(core.opponent(oplayer))

                    # 335.2 is the maximum score weighted
                    if mcount > ocount:
                        nscore = 335.2 - ocount
                    elif ocount > mcount:
                        nscore = mcount - 335.2
                    else:
                        nscore = 0
                    nspots_left = set()

            node[4].append([nscore, nboard, oppo, nspots_left, [], node, brackets, spot, -1, oppo+''.join(nboard)])

        lookupdict[node[9]] = node


def find_all_brackets(board, player, spots_left, core):
    brackets = {}
    for spot in spots_left:
        this_spot_brackets = {}
        for direction in oc.DIRECTIONS:
            bracket = core.find_bracket(spot, player, board, direction)
            if bracket is not None:
                this_spot_brackets[direction] = bracket
        if this_spot_brackets:
            brackets[spot] = this_spot_brackets
    return brackets


def score(board, player, core, matrix, nmoves):
    # matrix notation:
    # dict of all elements in sq, for each element:
    # 3-tuple
    #  0: amnt of points that place is usually worth
    #  1: set of spots that need to be non empty in order for
    #  2: amnt of points if requirements in 1 are ment
    oppo = core.opponent(player)
    cscore = 0
    mcount = 0
    ocount = 0
    for spot in sq:
        regular, req, special = matrix[spot]
        if board[spot] == player:
            if req and all(board[x] != oc.EMPTY for x in req):
                cscore += special
            else:
                cscore += regular
            mcount += 1
        elif board[spot] == oppo:
            if req and all(board[x] != oc.EMPTY for x in req):
                cscore -= special
            else:
                cscore -= regular
            ocount += 1
    if mcount + ocount == 64:
        if mcount > ocount:
            return 335.2 - ocount
        elif ocount > mcount:
            return mcount - 335.2
        else:
            return 0
    else:
        return cscore * (1 / (nmoves + 1) + 1)

if __name__=='__main__':
    mcore = my_core.MyCore()
    board = oc.OthelloCore().initial_board()
    tMatrix = load_matrix('C:/Users/Me/Documents/AI/othello/nmatrix.pkl')
    player = oc.BLACK
    spots_left = set(x for x in sq if board[x] == oc.EMPTY)
    startnode = [0, board, player, spots_left, [], None, find_all_brackets(board, player, spots_left, mcore), -1, -1, player+''.join(board)]
    move = abprune(startnode, mcore, 0, 7, tMatrix, -inf, inf, player, dict())[1]
    print(move)
    print(mcore.print_board(board))
