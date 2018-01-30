#strategy.py

EMPTY, BLACK, WHITE, OUTER = '.', '@', 'o', '?'
PLAYERS = {BLACK: 'Black', WHITE: 'White'}

class Strategy():

  def best_strategy(self, board, player, best_move, still_running):
    depth = 1
    while(True):
      best_move.value = self.my_search_strategy(board, player, depth)
      depth += 1

  def my_search_strategy(self, board, player, depth):
    pathHome = "./msg.txt"
    msgFile = open(pathHome, 'w')
    msgFile.write("hello\n")
    myBoard = [[0 for c in range(8)] for r in range(8)] 
    for r in range(8):
        for c in range(8):
            symbol = board[10*(r+1)+(c+1)]
            if   symbol == BLACK:  myBoard[r][c] = -1
            elif symbol == WHITE:  myBoard[r][c] = +1
            elif symbol == EMPTY:  myBoard[r][c] =  0
    if player == BLACK: maximizingPlayer = True
    else:               maximizingPlayer = False
    (r, c) = self.chooseMove(myBoard, maximizingPlayer, depth)
    return (r+1)*10+(c+1)

  directions = [(0, +1), (0, -1), (+1, 0), (-1, 0), (+1, -1), (+1, +1), (-1, -1), (-1, +1)]
  infinity = float("Infinity")

  def chooseMove(self, board, maximizingPlayer, depth):
    legalMoves = self.moves(board, maximizingPlayer)
    if maximizingPlayer: v = -self.infinity
    else: v = +infinity
    myMove = None
    for move in legalMoves:
      nextBoard = self.makeMove(self.copyIt(board), move, maximizingPlayer)
      val = self.alphabeta(nextBoard, depth, -self.infinity, self.infinity, not maximizingPlayer)
      if maximizingPlayer:
        if val > v: myMove, v = move, val
      else: 
        if val < v: myMove, v = move, val
    return myMove

  def copyIt(self, board):
    return [[board[r][c] for c in range(8)] for r in range(8)]

  def makeMove(self, board, move, maximizingPlayer):
    if move is None: return board
    r, c = move[0], move[1]
    if maximizingPlayer: token = -1
    else: token = +1
    board[r][c] = token
    for (dr, dc) in self.directions:
      r1, c1 = r + dr, c + dc
      if not (0 <= r1 < 8 and 0 <= c1 < 8): continue
      if board[r1][c1] != -token: continue
      while 0 <= r1 < 8 and 0 <= c1 < 8 and board[r1][c1] == -token:
        r1, c1 = r1 + dr, c1 + dc
      if not (0 <= r1 < 8 and 0 <= c1 < 8): continue
      if board[r1][c1] != token: continue
      r1, c1 = r1 - dr, c1 - dc
      while board[r1][c1] == -token:
        board[r1][c1] = token
        r1, c1 = r1 - dr, c1 - dc
    return board
  
  def moves(self, board, maximizingPlayer):
    returnList = [] # list of pairs (r,c)
    if maximizingPlayer: token = -1
    else: token = +1
    for r in range(8):
      for c in range(8):
        if board[r][c] != 0: continue
        for (dr, dc) in self.directions:
          r1, c1 = r + dr, c + dc
          if not (0 <= r1 < 8 and 0 <= c1 < 8): continue
          if board[r1][c1] != -token: continue
          while 0 <= r1 < 8 and 0 <= c1 < 8 and board[r1][c1] == -token:
            r1, c1 = r1 + dr, c1 + dc
          if not (0 <= r1 < 8 and 0 <= c1 < 8): continue
          if board[r1][c1] != token: continue
          returnList += [(r, c)]
    return returnList

  def finalGameValue(self, board):
    sum = 0
    for r in range(8):
      for c in range(8): 
        if board[r][c] == -1: sum += 1
        elif board[r][c] == +1: sum -= 1
    if sum > 0: return +10000
    if sum < 0: return -10000
    return 0

  def heuristicGameValue(self, board):
    sum = 10*(len(self.moves(board,True))-len(self.moves(board,False)))
    for r in [0, 7]:
      for c in [0, 7]:
        if board[r][c] == -1: sum += 75
        elif board[r][c] == +1: sum -= 75
    for r in [1, 6]:
      for c in [1, 6]:
        if board[r][c] == -1: sum -= 25
        elif board[r][c] == +1: sum += 25
    for r in [2, 5]:
      for c in [2, 5]:
        if board[r][c] == -1: sum += 12
        elif board[r][c] == +1: sum -= 12
    return sum

  def alphabeta(self, board, depth, alpha, beta, maximizingPlayer):
    maxMoves = self.moves(board, True)
    minMoves = self.moves(board, False)
    if len(maxMoves) == 0 and len(minMoves) == 0: return self.finalGameValue(board)
    if depth == 0: return self.heuristicGameValue(board)
    if maximizingPlayer:  legalMoves = maxMoves
    else: legalMoves = minMoves
    if len(legalMoves) == 0: return self.alphabeta(self.copyIt(board), depth-1, alpha, beta, not maximizingPlayer)
    if maximizingPlayer:
      v = -self.infinity
      for move in legalMoves:
        newboard = self.makeMove(self.copyIt(board), move, True)
        val = self.alphabeta(newboard, depth-1, alpha, beta, False)
        if val > v: v, bestMove = val, move
        alpha = max(alpha, v)
        if beta <= alpha: break
      return v
    else:
      v = self.infinity
      for move in legalMoves:
        newboard = self.makeMove(self.copyIt(board), move, False)
        val = self.alphabeta(newboard, depth-1, alpha, beta, True)
        if val < v: v, bestMove = val, move
        beta = min(beta, v) 
        if beta <= alpha: break
      return v

#end of python file
