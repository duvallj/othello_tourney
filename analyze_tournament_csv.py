import argparse
import csv
import os
from othello.gamescheduler.othello_core import BLACK, WHITE

def load_csv(filename):
    if not (os.path.exists(filename) and os.path.isfile(filename)):
        raise FileNotFoundError(filename)

    with open(filename, 'r') as f:
        infile = csv.DictReader(f)
        results = [row for row in infile]

    return results

def analyze_rr(results):
    num_wins = dict()
    for result in results:
        black_ai = result['Black']
        white_ai = result['White']
        winner = result['Winner']
        
        black_wins = num_wins.get(black_ai, 0)
        white_wins = num_wins.get(white_ai, 0)

        if winner == BLACK:
            num_wins[black_ai] = black_wins + 1
        elif winner == WHITE:
            num_wins[white_ai] = white_wins + 1

    top_num = input("How many top AIs to show? [default=8]: ")
    try:
        top_num = int(top_num)
    except ValueError:
        print("Invalid number, defaulting to 8...")
        top_num = 8

        output = sorted(num_wins.items(), key=lambda i: -i[1])[:top_num]

    for ai, num in output:
        print("{}: {}".format(ai, num))

def analyze_bracket(results):
    # TODO: once you fully implement bracket sets, come back to this
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
    else:
        raise ValueError("'{}' is not a valid tournament type!".format(args.tournament_type))
