#
# p0g.py by Peter Gabor
# for Othello testing purposes
# 15 Jan 2018
# Minimal corner strategy
#
import sys, time, math, random, multiprocessing

# Debugging info
from os import path
import re

# pyver = re.sub(' [^Z]*', "", sys.version)        
# print ("Python version {} running {}".format(pyver, path.basename(__file__)))


def legalMoves(othelloBoard, token):
  dot = '.'
  moves = {}
  for idx in [idx for idx,tkn in enumerate(othelloBoard) if tkn==dot]:
    for dir, lim in legalMoves.dirrng[idx]:
      for p in range(idx+dir,lim,dir):
        if othelloBoard[p]==".": break
        if othelloBoard[p]==token:
          if p==idx+dir: break
          if idx not in moves: moves[idx] = set()
          moves[idx].update(range(idx+dir,p,dir))
          break
  return moves


def makeMove(board, token, mv, affects):
  # affects are the positions of enemy tokens which flip
  for i in affects:
    board = board[:i] + token + board[i+1:]
  return board[:mv] + token + board[mv+1:]


def showBoard(board, mvNum, player, token, mv):
  print("\nMove {}\nPlayer {} as {} moves to {}  ===> X:{} vs. O:{}".format(
             mvNum, player, token, mv, board.count(theX), board.count(theO)))
  print("\n".join([str(i+1) + "  " + " ".join(board[i*sL:i*sL+sL]) for i in range(sL)]))
  print("\n   A B C D E F G H\n")


def rngLim(c, d, n):
  if (abs(d) - 1) % (n-1):    # if diagonal direction
    return n-max(n-1-c%n if (d-1)%n else c%n, n-1-c//n if d<0 else c//n)
  return (n if d>0 else 1) - (d // abs(d)) * (c%n if d%n else c//n)


def findIdx(lst, pattern):
  # returns the first index where the regex matches, else -1
  for i, v in enumerate(lst):
    if re.search(pattern, v): return i
  return -1


def findIdxs(lst, pattern):
  # returns the indeces where the rgex matches, else []
  return [i for i, v in enumerate(lst) if re.search(pattern, v)]


class Strategy():
  def best_strategy(self, board, player, best_move, still_running):
    brd = "".join(board).replace("?", "").replace("@", "X").replace("o", "O")
    token = "X" if player=="@" else "O"

    sL = int(len(brd)**.5+.5)
    dirs = [{h+v for h in [-1,0,1] for v in [-sL,0,sL] for b in [c+h+v+h+v] \
                   if (b>=0)*(b<sL*sL)*((b%sL-c%sL)*h>=0)}-{0} for c in range(sL*sL)]
    # the direction together with the boundary of where one must check for bracketing
    legalMoves.dirrng = [[(dir,idx+rngLim(idx,dir,sL)*dir) for dir in setOfDirs] for idx,setOfDirs in enumerate(dirs)]


    mv = bestMoveHeuristic(brd, token)
    mv1 = 11 + (mv//8)*10 + (mv % 8)
    best_move.value = mv1

    global levelCt, leafCtr
    if board.count('.') <= levelCt:
      for lvl in range(1, levelCt+3, 2):
#        mm = negmaxAB(board, token, lvl, -maxNega*len(board), maxNega*len(board))
        mm = negmaxAB(brd, token, lvl, -len(brd), len(brd))
        print ("Negamax analysis shows: {}".format(mm))
        mv = mm[-1]
        mv1 = 11 + (mv//8)*10 + (mv % 8)
        print ("Move submission at lvl {} is {} => {}".format(lvl, mv, mv1))
        best_move.value = mv1









def main():
  global sL, dot, theX, theO
  help = "Usage: p0g.py [othelloBoard] [token] [moves ...]"
  args = sys.argv[1:]
  brdIdx = findIdx(args, "^[xXoO.]{3,}$")
  tknIdx = findIdx(args, "^[xXoO]$")
  mvIdxs = findIdxs(args, "^([a-hA-H][1-8]|[1-5]?\\d|6[0-3]|-[12])$")
  if (brdIdx>=0) + (tknIdx>=0) + len(mvIdxs) != len(args): exit(help)

  # Some, but not all of this is ready for other board dimensions.
  # For example, the regular expressions for finding moves is not reconciled
  # against sL, nor is there currently any way to specify sL from the command line

  board = args[brdIdx] if brdIdx>=0 else \
          dot * ((sL*sL-sL)//2-1) + theO + theX + dot * (sL-2) + theX + theO + dot * ((sL*sL-sL)//2-1)
  sL = int(len(board)**.5 + .5)     # in case of a board of a different size
  board = board.upper()
  token = args[tknIdx].upper() if tknIdx>=0 else (theO if board.count(dot)%2 else theX)
  print ("dot ct: {}, tknIdx: {}, token: {}".format(board.count(dot), tknIdx, token))

  lm = legalMoves(board, token)
  if not lm: token = theO if token==theX else theX

  # show starting board
  print("\n".join([str(i+1) + "  " + " ".join(board[i*sL:i*sL+sL]) for i in range(sL)]))
  print("\n   A B C D E F G H\n")

  # now make the moves specified in the move sequence
  for i, mvIdx in enumerate(mvIdxs):
    mv = args[mvIdx]
    # get a numeric value for the move
    if mv[0] == "-": continue            # an FYI entry
    if len(mv)>1 and ord(mv[0])>57: mv = (ord(mv[0])-ord('A'))+8*(int(mv[1])-1)  
    else: mv=int(mv)

    lm = legalMoves(board, token)
    if not lm:
      print ("{} must pass\n\n".format(token))
      token = theO if token==theX else theX
      lm = legalMoves(board, token)
      if not lm:
        exit ("and {} must pass - premature game over")

    if mv not in lm:
      exit("{} is an illegal move at this point. The possibilities are: {}".format(mv, lm.keys()))

    board = makeMove(board, token, mv, lm[mv])
    showBoard(board, i+1, "", token, mv)
    token = theO if token==theX else theX


  print (board)
  lm = legalMoves(board, token)
  if not lm:
    print("There are no legal moves available for {}".format(token))
    exit()
  print ("The legal moves for {} are {}".format(token, lm.keys()))

  mv = bestMoveHeuristic(board, token)
  print ("My heuristic choice is {}".format(mv))

  global levelCt, leafCtr
  if board.count('.') <= levelCt:
    for lvl in range(1, levelCt+3, 2):
#      print("\nRunning negamax at level {}".format(lvl))
      mm = negmaxAB(board, token, lvl, -len(board), len(board))
#      mm = negmaxAB(board, token, lvl, -maxNega*len(board), maxNega*len(board))
      mv = mm[-1]
      print ("At level {}, after {} leafs and negamax {}, my choice is {}".format(lvl, leafCtr, mm, mv), flush=True)



def negmaxAB(brd, token, levels, improvableBound, hardBound):
  # evaluate the best move from token's point of view
  # returns a list where the first element is the evaluation of the board
  # and the remaining elements are the moves in reverse order leading to that evaluation
  enemy = "O" if token=="X" else "X"
  global leafCtr
  if not levels: leafCtr += 1; return [boardEval(brd, token)]
  
#  print ("lm check in Negamax with {} {}".format(brd, token))
  lm = legalMoves(brd, token)
  if not lm:
    lm2 = legalMoves(brd, enemy)
    # -2 signifies end of game.  It will dominate non end of game values
#    if not lm2: leafCtr += 1; return [maxNega * (brd.count(token) - brd.count(enemy)), -2]
    if not lm2: leafCtr += 1; return [brd.count(token) - brd.count(enemy), -3]          # -3 means game end
    mm = negmaxAB(brd, enemy, levels-1, -hardBound, -improvableBound) + [-1]  # else it's a pass
#    print ("level {}, improvableBound {}, hardBound {}, negamax => {}".format(levels, improvableBound, hardBound, mm))
    return [-mm[0]] + mm[1:]

  mmSave = []
  for mv in lm:
    mm = negmaxAB(makeMove(brd, token, mv, lm[mv]), enemy, levels-1, -hardBound, -improvableBound) + [mv]
#    if levels: print ("mustBeAtLeast: {}, noMoreThan: {}\nalphaBeta: {}\n".format(mustBeAtLeast, noMoreThan, mm))
    mmscore = -mm[0]
#    print ("Level {}, improvableBound {}, hardBound {}, score: {}, nm moves => {}".format(levels, improvableBound, hardBound, mmscore, mm[1:]))
    if (mmscore != hardBound) and ((hardBound==improvableBound) or (mmscore>hardBound)==(hardBound>improvableBound)):
#      print ("Pruning remaining branches")
      return [mmscore] + mm[1:]                # nothing more to do
    if (mmscore==improvableBound) or (mmscore==hardBound) or (mmscore > improvableBound)==(mmscore < hardBound):
#      print ("Improvable-Hard bounds of {}-{} met with {}, best updated to {}".format(improvableBound, hardBound, mmscore, mm[1:]))
      improvableBound = mmscore
      mmSave = [mmscore] + mm[1:]              # an improvement
#    else: print("Branch with score of {} did not meet improveable bound of {} - marked for obsolesence".format(mmscore, improvableBound))
  if not mmSave:
#    print ("Lower bound of {} unmet - returning most recent negamax {}: {}".format(improvableBound, mmscore, mm[1:]))
    mmSave = [mmscore] + mm[1:]                             # just in case nothing is satisfactory
  return mmSave






def boardEval(brd, token):
  myTokens = {pos for pos, tkn in enumerate(brd) if tkn==token}
  enemy = "O" if token=="X" else "X"
  enemyTokens = {pos for pos, tkn in enumerate(brd) if tkn==enemy}
  return len(myTokens) - len(enemyTokens)

  cxMine = {cx for c in corners for cx in dctcx[c] if brd[c]!=token and brd[cx]==token}
  cxEnemy = {cx for c in corners for cx in dctcx[c] if brd[c]!=enemy and brd[cx]==enemy}
  return +     len(myTokens)            - len(enemyTokens) \
         + 6 * (len(myTokens & corners) - len(enemyTokens & corners)) \
         - 4 * (len(cxMine)             + len(cxEnemy))


'''
def negmaxAB(brd, token, levels, mustBeAtLeast, noMoreThan):
  # evaluate the best move from token's point of view
  # returns a list where the first element is the evaluation of the board
  # and the remaining elements are the moves in reverse order leading to that evaluation
  enemy = "O" if token=="X" else "X"
  global leafCtr
  if not levels: leafCtr += 1; return [boardEval(brd, token)]
  
  lm = legalMoves(brd, token)
  if not lm:
    lm2 = legalMoves(brd, enemy)
    # -2 signifies end of game.  It will dominate non end of game values
#    if not lm2: leafCtr += 1; return [maxNega * (brd.count(token) - brd.count(enemy)), -2]
    if not lm2: leafCtr += 1; return [brd.count(token) - brd.count(enemy), -3]          # -3 means game end
    mm = negmaxAB(brd, enemy, levels-1, -noMoreThan, -mustBeAtLeast) + [-1]  # else it's a pass
    print ("level {}, mustBeAtLeast {}, noMoreThan {}, negamax => {}".format(levels, mustBeAtLeast, noMoreThan, mm))
    return [-mm[0]] + mm[1:]

  mmSave = []
  for mv in lm:
    mm = negmaxAB(makeMove(brd, token, mv, lm[mv]), enemy, levels-1, -noMoreThan, -mustBeAtLeast) + [mv]
#    if levels: print ("mustBeAtLeast: {}, noMoreThan: {}\nalphaBeta: {}\n".format(mustBeAtLeast, noMoreThan, mm))
    mmscore = -mm[0]
    print ("Level {}, mustBeAtLeast {}, noMoreThan {}, score: {}, nm moves => {}".format(levels, mustBeAtLeast, noMoreThan, mmscore, mm[1:]))
    if mmscore >= noMoreThan: print("Pruning remaining branches"); return [mmscore] + mm[1:]     # nothing more to do
    if mmscore >= mustBeAtLeast:
      mustBeAtLeast = mmscore
      print ("Bounds met, best updated")
      mmSave = [mmscore] + mm[1:]
  if not mmSave:
    print ("Lower bound unmet - returning most recent negamax")
    mmSave = [mmscore] + mm[1:]                             # just in case nothing is satisfactory
  return mmSave
'''




# maxNega = len(board) + 10 * 4 # len(board) + (6+4) * cornersCt
leafCtr = 0
# levelCt = 3
'''
for lvl in range(1,2*levelCt,2):
  mm = negmaxAB(board, token, lvl, -maxNega*len(board), maxNega*len(board))
  print ("After {} leafs, and negamax {}, my choice is {}".format(leafCtr, mm, mm[-1]), flush=True)
exit()
'''


def bestMoveHeuristic(board, token):

  lm = legalMoves(board, token)
  lms = {*lm.keys()}

  # improvement 1: safe play: corner
  if corners & lms: lms &= corners


  # for i in corners: dctE[i] = {i}
  safeEdges = set()
  for t in dctE.keys() & lms:
    brd = makeMove(board, token, t, lm[t])
    for c in dctE[t]:
      dir = ((c>t)-(c<t)) * (1 if (c-t)%sL else sL)
#      if not dir: p=c; break
      for p in range(t+dir,c+dir,dir):
        if brd[p]!=token: break
      if p==c and brd[c]==token: safeEdges.add(t); break
  if safeEdges & lms: lms &= safeEdges


  # improvement 3: don't play to cx unless corner is protected
  cx = {p for c in dctcx for p in dctcx[c] if board[c]!=token}
  if lms - cx: lms = lms - cx


  '''
  # old improvement 4: play center rather than edges (unless the edges are stable):
  # if board.count(dot)>len(board)//2 and 
  # print ("EandC: {}\nrestricted legal moves: {}".format(EandC, lms - EandC))
  if lms - EandC: lms -= EandC
  '''

  # improvement 4: from among the choices, order by enemy mobility and pick the least one
  # but view allowing the enemey a chance at a coner very dimly (by adding a large number to mobility score)
  enemy = "O" if token=="X" else "X"
  enemyMobilityList = sorted([(len(lm2) + 10*len(corners & {*lm2}), mv) \
      for mv in lms for lm2 in [legalMoves(makeMove(board, token, mv, lm[mv]), enemy)]])
  enemyMobilityListWinnowed = [lmt for lmt in enemyMobilityList if lmt[0]==enemyMobilityList[0][0]]
  best = random.choice(enemyMobilityListWinnowed)
  print ("From among {}, my choice is {}".format(enemyMobilityList, best))
  return best[-1]


# lms2 = [(len(legalMoves(makeMove(board, token, mv, lm[mv]), "O" if token=="X" else "X")), mv) for mv in lms]
# lms2.sort()
# minlen = lms2[0][0]
# lms2 = [tpl for tpl in lms2 if tpl[0]==minlen]
#  print ("My choice is {}".format(random.choice(lms2)[1]))
# exit()

# print ("My choice is {}".format(random.choice([*lms])))



sL       = 8    # side length of board
theX, theO, dot = "X", "O", "."
levelCt = 13
# the set of directions in which one can go for making moves
dirs = [{h+v for h in [-1,0,1] for v in [-sL,0,sL] for b in [c+h+v+h+v] \
                   if (b>=0)*(b<sL*sL)*((b%sL-c%sL)*h>=0)}-{0} for c in range(sL*sL)]
# the direction together with the boundary of where one must check for bracketing
legalMoves.dirrng = [[(dir,idx+rngLim(idx,dir,sL)*dir) for dir in setOfDirs] for idx,setOfDirs in enumerate(dirs)]

corners = {0, sL*sL-1, sL-1, sL*sL-sL}

dctE = {i:{0,sL-1} for i in range(1,sL-1)}
# improvement 2: safe play to: edge position that connects to a safe corner
for i in range(sL,sL*sL-sL,sL): dctE[i] = {0, sL*sL-sL}
for i in range(sL*sL-sL+1,sL*sL-1): dctE[i] = {sL*sL-sL, sL*sL-1}
for i in range(sL-1+sL, sL*sL-1, sL): dctE[i] = {sL-1, sL*sL-1}

EandC = {*dctE.keys()} | corners

dctcx =     {0: {1, sL, sL+1}, sL-1:{sL-2, sL+sL-1, sL+sL-2}, sL*sL-1:{sL*sL-2, sL*sL-sL-1, sL*sL-sL-2},
      sL*sL-sL: {sL*sL-sL+1, sL*sL-sL-sL, sL*sL-sL-sL+1}}





if __name__ == "__main__":
  multiprocessing.freeze_support()
  main()
