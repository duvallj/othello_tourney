import Othello_Core as oc


class MyCore(oc.OthelloCore):
    def __init__(self):
        self.sq = self.squares()
        self.reset()
        self.players = oc.BLACK + oc.WHITE
        # self.scCount = 0

    def reset(self):
        self.moves = {oc.WHITE: None, oc.BLACK: None}
        self.brackets = {oc.WHITE: {}, oc.BLACK: {}}

    def is_valid(self, move, board):
        """Is move a square on the board?"""
        return board[move] == oc.EMPTY

    def opponent(self, player):
        """Get player's opponent piece."""
        return self.players[player == oc.BLACK]

    def find_bracket(self, square, player, board, direction):
        """
        Find a square that forms a bracket with `square` for `player` in the given
        `direction`.  Returns None if no such square exists.
        Returns the index of the bracketing square if found
        """

        current = square + direction
        opponent = self.opponent(player)
        inbetween = False

        while board[current] == opponent:
            current += direction
            inbetween = True

        toreturn = None

        if board[current] == player and inbetween:
            toreturn = current

        return toreturn

    def is_legal(self, move, player, board):
        """Is this a legal move for the player?"""
        if not self.is_valid(move, board):
            return False
        for direction in oc.DIRECTIONS:
            bracket = self.find_bracket(move, player, board, direction)
            if bracket is not None:
                return True
        return False

    ### Making moves

    # When the player makes a move, we need to update the board and flip all the
    # bracketed pieces.

    def make_move(self, move, player, board, real=True):
        """Update the board to reflect the move by the specified player."""
        if not self.is_valid(move, board):
            return False
        toreturn = False
        for direction in oc.DIRECTIONS:
            toreturn = self.make_flips(move, player, board, direction) or toreturn
        if toreturn:
            board[move] = player
        if real:
            self.reset()
        return toreturn

    def make_flips(self, move, player, board, direction):
        """Flip pieces in the given direction as a result of the move by player."""
        oend = self.find_bracket(move, player, board, direction)
        if oend is None:
            return False
        spot = move
        while spot != oend:
            spot += direction
            board[spot] = player
        return True

    def legal_moves(self, player, board):
        """Get a list of all legal moves for player, as a list of integers"""
        if self.moves[player] is not None:
            return self.moves[player]
        else:
            moves = [spot for spot in self.sq if self.is_legal(spot, player, board)]
            self.moves[player] = moves
            return moves

    def any_legal_move(self, player, board):
        """Can player make any moves? Returns a boolean"""
        return bool(self.legal_moves(player, board))

    def next_player(self, board, prev_player):
        """Which player should move next?  Returns None if no legal moves exist."""
        nplayer = self.opponent(prev_player)
        if self.any_legal_move(nplayer, board):
            return nplayer
        elif self.any_legal_move(prev_player, board):
            return prev_player
        else:
            return None

    def score(self, player, board):
        """Compute player's score (number of player's pieces minus opponent's)."""
        return board.count(player) - board.count(self.opponent(player))