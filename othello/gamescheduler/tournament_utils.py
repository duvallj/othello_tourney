from asyncio import Future
import itertools

from .othello_core import BLACK, WHITE, EMPTY


class GameData:
    """
    Utility class to store information about a game
    """
    def __init__(self, black, white): 
        # Should be the index of the game in the larger list.
        # Is set when exporting the list of games
        self.num = -1

        # Should be strings of AIs
        assert(isinstance(black, str))
        assert(isinstance(white, str))
        self.black = black
        self.white = white
        
        # Should be integers with the scores of the game
        self.black_score = 0
        self.white_score = 0

        # Should be BLACK, WHITE, or EMPTY
        self.winner = EMPTY
        # Boolean determining whether the win was by a forfeit
        self.by_forfeit = False

class SetData:
    """
    Utility class to store information about sets of games
    """

    # Black and white only used as differentiators, games between
    # can be of any color
    def __init__(self, black, white, black_from_set=None, white_from_set=None,\
            winner_set=None, loser_set=None):
        # Index of set in list, again set when exporting
        self.num = -1
        # Flag to see whether or not the set has been played
        self.played = False
        
        # Should be strings of AIs
        assert(isinstance(black, str))
        assert(isinstance(white, str))
        self.black = black
        self.white = white

        # List of games played within the set
        self.games = []

        # Should be other SetData objects
        assert(black_from_set is None or isinstance(black_from_set, SetData))
        assert(white_from_set is None or isinstance(white_from_set, SetData))
        self.black_from_set = black_from_set
        self.white_from_set = white_from_set

        # Information about where the winners and losers head to next
        assert(winner_set is None or isinstance(winner_set, SetData))
        assert(loser_set is None or isinstance(loser_set, SetData))
        self.winner_set = winner_set
        self.loser_set = loser_set

    def add_game(self, game):
        if (game.black != self.black or game.white != self.white) and \
                (game.black != self.white or game.white != self.black):
            raise ValueError("Tried to add a game ({} vs {}) to a set with different AIs! ({} vs {})".format(game.black, game.white, self.black, self.white))

        self.games.append(game)

    def get_overall_winner(self):
        # These variables are ordered by importance for determining overall winner
        black_wins = 0
        white_wins = 0
        black_forfeits = 0
        white_forfeits = 0
        black_differential = 0
        white_differential = 0

        for game in self.games:
            if game.black == self.black:
                assert(game.white == self.white)
                if game.winner == BLACK:
                    black_wins += 1
                    if game.by_forfeit:
                        white_forfeits += 1
                elif game.winner == WHITE:
                    white_wins += 1
                    if game.by_forfeit:
                        white_forfeits += 1
                black_differential += game.black_score
                white_differential += game.white_score
            else:
                assert(game.black == self.white)
                assert(game.white == self.black)
                # Same as above, only all variable names swapped
                if game.winner == BLACK:
                    white_wins += 1
                    if game.by_forfeit:
                        black_forfeits += 1
                elif game.winner == WHITE:
                    black_wins += 1
                    if game.by_forfeit:
                        white_forfeits += 1
                white_differential += game.black_score
                black_differential += game.white_score

        # First, compare by number of wins
        if black_wins > white_wins:
            return BLACK
        elif white_wins > black_wins:
            return WHITE
        else:
            # If that fails, take the person with less forfeits
            if black_forfeits < white_forfeits:
                return BLACK
            elif white_forfeits < black_forfeits:
                return WHITE
            else:
                # If that also fails, go by piece differential
                if black_differential > white_differential:
                    return BLACK
                elif white_differential > black_differential:
                    return WHITE
                else:
                    # If all those fail, it's really a tie
                    return EMPTY


def create_single_elim_bracket(ai_list):
    """
    Arguments:
        ai_list : list
            All the AIs, in seeded order, to create the bracket from

    Returns:
        A list of sets that need to be played, two games for each (one for
        each AI starting)
    """
    pass

def create_round_robin(ai_list):
    """
    Identical to above, only creates a round-robin tournament instead.
    """
    output = []
    for black, white in itertools.combinations(ai_list, 2):
        output.append(SetData(black, white))

    return output

def create_everyone_vs(ai_list, who="random"):
    """
    Matches everyone against a baseline player (usually random)
    """
    output = []
    for black in ai_list:
        if black != who:
            output.append(SetData(black, who))

    return output

class ResultsCSVWriter:
    """
    A class that writes tournament results (list of SetData objects) to a CSV file
    """
    def __init__(self, name):
        self.sets_filename = name+"_sets.csv"
        self.games_filename = name+"_games.csv"
        
    def write(self, set_results):
        with open(self.sets_filename, "w") as sfout, \
                open(self.games_filename, "w") as gfout:
            sfout.write("Set_Num,Black,Black_From_Set,White,White_From_Set,Winner,Winner_Set,Loser_Set\n")
            gfout.write("Black,White,Black_Score,White_Score,Winner,By_Forfeit\n")
            
            for i in range(len(set_results)):
                set_results[i].num = i

            for s in set_results:
                sfout.write(f"{s.num},{s.black},{s.black_from_set.num if s.black_from_set else 'None'},{s.white},{s.white_from_set.num if s.white_from_set else 'None'},{s.get_overall_winner()},{s.winner_set.num if s.winner_set else 'None'},{s.loser_set.num if s.loser_set else 'None'}\n")
                for game in s.games:
                    gfout.write(f"{game.black},{game.white},{game.black_score},{game.white_score},{game.winner},{game.by_forfeit}\n")


