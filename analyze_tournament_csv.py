import argparse
import csv
import os
from othello.gamescheduler.othello_core import BLACK, WHITE

def load_csv(filename):
    if not (os.path.exists(filename) and os.path.isfile(filename)):
        raise FileNotFoundError(filename)

    with open(filename, 'r') as f:
        infile = csv.DictReader(f,['Black','White','Black_Score','White_Score','Winner','By_Forfeit'])
        results = [tuple(row) for row in infile.reader]

    return results

def analyze_rr(results):
    num_wins = dict()
    differential = dict()
    for black_ai, white_ai, black_score, white_score, winner, forfeit in results:
        black_wins = num_wins.get(black_ai, 0)
        white_wins = num_wins.get(white_ai, 0)
        black_diff = differential.get(black_ai, 0)
        white_diff = differential.get(white_ai, 0)

        if winner == BLACK:
            num_wins[black_ai] = black_wins + 1
        elif winner == WHITE:
            num_wins[white_ai] = white_wins + 1

        if not forfeit:
            differential[black_ai] = black_diff + black_score - white_score
            differential[white_ai] = white_diff + white_score - black_score

    possible_filters = {'w', 'd', 'p'}
    filter_type = input("Filter by Wins or piece Differential? [W/d]: ")
    if not filter_type: filter_type = 'w'
    filter_type = filter_type[0].lower()
    while not (filter_type in possible_filters):
        print("Invalid filter type!")
        filter_type = input("Filter by Wins or piece Differential? [W/d]: ")
        if not filter_type: filter_type = 'w'
        filter_type = filter_type[0].lower()

    top_num = input("How many top AIs to show? [default=8]: ")
    try:
        top_num = int(top_num)
    except ValueError:
        print("Invalid number, defaulting to 8...")
        top_num = 8

    if filter_type == 'w':
        output = sorted(num_wins.items(), key=lambda i: -i[1])[:top_num]
    else:
        output = sorted(differential.items(), key=lambda i: -i[1])[:top_num]

    for ai, num in output:
        print("{}: {}".format(ai, num))

def analyze_bracket(results):
    # TODO: not entirely sure how to do this w/ the current structure of output,
    # maybe want to redo that?
    """
    num_places = input("Enter the number of places you would like to calculate [default=4]: ")
    try:
        num_places = int(num_places)
    except ValueError:
        print("Invalid number, defaulting to 4...")
        num_places = 4

    place = 1
    actual_game = len(results) - 1
    while place <= num_places and actual_game >= 0:
        black_ai, white_ai, black_score, white_score, winner, forfeit = \
                results[actual_game]

        actual_game -= 1
    """
    pass

def analyze_pools(results):
    pass

def make_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('tournament_type', type=str,
            help="The type of tournament file to analyze")

    parser.add_argument('file', type=str,
            help="The filename of the tournament to analyze")

    return parser


if __name__ == "__main__":
    args = make_parser().parse_args()

    results = load_csv(args.file)

    if args.tournament_type == "rr":
        analyze_rr(results)
    elif args.tournament_type == "bracket":
        analyze_bracket(results)
    elif args.tournament_type == "pools":
        analyze_pools(results)
    else:
        raise ValueError("'{}' is not a valid tournament type!".format(args.tournament_type))
