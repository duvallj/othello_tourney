from asyncio import Future
import itertools

from ...gamescheduler.othello_core import BLACK, WHITE, EMPTY, BORDER
from .models import GameModel, SetModel, PlayerModel

# TODO: Make this all specific to a tournament by setting the 
# `in_tournament` field of all the sets you add (eventually)

def add_game_to_set(setm, game):
    if (game.black != setm.black or game.white != setm.white) and \
            (game.black != setm.white or game.white != setm.black):
        raise ValueError("Tried to add a game ({} vs {}) to a set with different AIs! ({} vs {})".format(game.black, game.white, setm.black, setm.white))

    game.in_set = setm
    game.save()
 
def calc_set_winner(setm):
    # These variables are ordered by importance for determining overall winner
    black_wins = 0
    white_wins = 0
    black_forfeits = 0
    white_forfeits = 0
    black_differential = 0
    white_differential = 0

    for game in setm.games.all():
        if game.black == setm.black:
            assert(game.white == setm.white)
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
            assert(game.black == setm.white)
            assert(game.white == setm.black)
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
        setm.winner = BLACK
    elif white_wins > black_wins:
        setm.winner = WHITE
    else:
        # If that fails, take the person with less forfeits
        if black_forfeits < white_forfeits:
            setm.winner = BLACK
        elif white_forfeits < black_forfeits:
            setm.winner = WHITE
        else:
            # If that also fails, go by piece differential
            if black_differential > white_differential:
                setm.winner = BLACK
            elif white_differential > black_differential:
                setm.winner = WHITE
            else:
                # If all those fail, it's really a tie
                setm.winner = EMPTY

    setm.save()

# Allows adding player v player, player v winner of set, or winners of sets together
def create_set(black_item, white_item, *, black_winner=True, white_winner=True):
    new_set = SetData()
    if isinstance(black_item, SetModel):
        if isinstance(white_item, SetModel):
            new_set.black_from_set = black_item
            new_set.white_from_set = white_item
            
            if black_winner:
                black_item.winner_set = new_set
            else:
                black_item.loser_set = new_set
            black_item.save()
            if white_winner:
                white_item.winner_set = new_set
            else:
                white_item.loser_set = new_set
            white_item.save()
        else:
            assert(isinstance(white_item, PlayerModel))
            
            new_set.black_from_item = black_item
            new_set.white = white_item

            if black_winner:
                black_item.winner_set = new_set
            else:
                black_item.loser_set = new_set
            black_item.save()
    else:
        assert(isinstance(black_item, PlayerModel))
        if isinstance(white_item, SetModel):
            new_set.black = black_item
            new_set.white_from_set = white_item

            if white_winner:
                white_item.winner_set = new_set
            else:
                white_item.loser_set = new_set
            white_item.save()
        else:
            assert(isinstance(white_item, PlayerModel))
            new_set.black = black_item
            new_set.white = white_item

    new_set.save()
    return new_set

# Gets (or creates) a PlayerModel object from the player id string
def get_player(player_id):
    obj, created = PlayerModel.objects.get_or_create(
            name=player_id)
    return obj


def create_single_elim_round_helper(set_list):
    out_sets = []
    if len(set_list) % 2 == 0:
        for i in range(len(set_list)//2):
            set1 = set_list[i]
            set2 = set_list[len(set_list)-i-1]
            out_sets.append(create_set(set1, set2))
    # If we have an odd number, let the first seed have a bye
    else:
        for i in range(1, len(set_list)//2+1):
            set1 = set_list[i]
            set2 = set_list[len(set_list)-i]
            out_sets.append(create_set(set1, set2))
        # This is equivalent to a bye b/c their game is included in the next round
        out_sets.append(set_list[0])

    return out_sets

def create_single_elim_bracket(ai_list):
    """
    Arguments:
        ai_list : list
            All the AIs, in seeded order, to create the bracket from

    Returns:
        A list of sets that need to be played, two games for each (one for
        each AI starting)
    """
    if len(ai_list) <= 1:
        return []

    overall_sets = []
    current_sets = [get_player(player) for player in ai_list]
    next_sets = []
    
    while len(current_sets) > 1:
        next_sets = create_single_elim_round_helper(current_sets)
        overall_sets.extend(next_sets)
        current_sets = next_sets

    return overall_sets

def create_round_robin(ai_list):
    """
    Identical to above, only creates a round-robin tournament instead.
    """
    output = []
    act_ai_list = [get_player(player) for player in ai_list]
    for black, white in itertools.combinations(act_ai_list, 2):
        output.append(create_set(black, white))

    return output

def create_everyone_vs(ai_list, who="random"):
    """
    Matches everyone against a baseline player (usually random)
    """
    output = []
    act_ai_list = [get_player(player) for player in ai_list]
    act_who = get_player(who)
    for black in act_ai_list:
        if black.name != who.name:
            output.append(create_set(black, who))

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
                SetModelUtil().calc_overall_winner(s)
                sfout.write(f"{s.id},{s.black},{s.black_from_set.id if s.black_from_set else 'None'},{s.white},{s.white_from_set.id if s.white_from_set else 'None'},{s.winner},{s.winner_set.id if s.winner_set else 'None'},{s.loser_set.id if s.loser_set else 'None'}\n")
                for game in s.games:
                    gfout.write(f"{game.black},{game.white},{game.black_score},{game.white_score},{game.winner},{game.by_forfeit}\n")


