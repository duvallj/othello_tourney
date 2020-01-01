import argparse
import csv
import os
from othello.gamescheduler.othello_core import BLACK, WHITE

def load_csv(filename):
    """
    Reads each row of a CSV into a list using a DictReader
    """
    if not (os.path.exists(filename) and os.path.isfile(filename)):
        raise FileNotFoundError(filename)

    with open(filename, 'r') as f:
        infile = csv.DictReader(f)
        results = [row for row in infile]

    return results

def read_rankings(filename):
    """
    Reads tournament rankings from a file
    
    Newline-seperated list of names, ordered from "best"
    rank at the top to lowest rank at the bottom.
    """
    ranking = [] # first index is highest rank
    with open(filename, 'r') as f:
        ranking = [line.strip() for line in f if line.strip()]
    return ranking

def write_rankings(filename, rankings):
    """
    Writes tournament rankings to a file, same format as reading
    """
    with open(filename, 'w') as f:
        for name in rankings:
            f.write("{}\n".format(name))

def analyze_stats(results):
    num_wins = dict()
    differentials = dict()
    for result in results:
        black_ai = result['Black']
        white_ai = result['White']
        winner = result['Winner']
        
        black_differential = differentials.get(black_ai, 0)
        white_differential = differentials.get(white_ai, 0)
        black_wins = num_wins.get(black_ai, 0)
        white_wins = num_wins.get(white_ai, 0)

        if winner == BLACK:
            num_wins[black_ai] = black_wins + 1
            num_wins[white_ai] = white_wins
        elif winner == WHITE:
            num_wins[white_ai] = white_wins + 1
            num_wins[black_ai] = black_wins

        if result.get('Black_Score', False):
            diff = int(result['Black_Score']) - int(result['White_Score'])
            differentials[black_ai] = black_differential + diff
            differentials[white_ai] = white_differential - diff
    
    return num_wins, differentials

def show_top_wins(num_wins):
    top_num = input("How many top AIs to show? [default=8]: ")
    try:
        top_num = int(top_num)
    except ValueError:
        print("Invalid number, defaulting to 8...")
        top_num = 8

    output = sorted(num_wins.items(), key=lambda i: -i[1])[:top_num]

    for ai, num in output:
        print("{}: {}".format(ai, num))

def order_by_wins(results, args):
    num_wins, _ = analyze_stats(results)
    ranking = []
    if args.in_ranking:
        ranking = read_rankings(args.in_ranking)
    else:
        # No previous ranking, use alphabetical order
        ranking = sorted([name for name in num_wins.keys()])
    
    # Sort by most wins at the front
    # Python's sort is stable, so this is fine
    new_ranking = sorted(ranking, key=lambda i: -num_wins[i])

    if args.out_ranking:
        write_rankings(args.out_ranking, new_ranking)
    else:
        print("\n".join(new_ranking))

def order_by_differential(results, args):
    _, differential = analyze_stats(results)
    ranking = []
    if args.in_ranking:
        ranking = read_rankings(args.in_ranking)
    else:
        # No previous ranking, use alphabetical order
        ranking = sorted([name for name in differential.keys()])
    
    # Sort by most wins at the front
    # Python's sort is stable, so this is fine
    new_ranking = sorted(ranking, key=lambda i: -differential[i])

    if args.out_ranking:
        write_rankings(args.out_ranking, new_ranking)
    else:
        print("\n".join(new_ranking))


def analyze_bracket(results):
    # TODO: once you fully implement bracket sets, come back to this
    pass

ANALYSIS_TYPES = ["wins", "differential"]
ANALYSIS_FUNCS = [order_by_wins, order_by_differential]
assert(len(ANALYSIS_TYPES) == len(ANALYSIS_FUNCS))

def make_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('analysis_type', type=str, choices=ANALYSIS_TYPES,
            help="The type of analysis to perform")

    parser.add_argument('file', type=str,
            help="The filename of the tournament to analyze")

    parser.add_argument("--in-ranking", type=str,
            help="Previous rankings to read from, used in certain analysis types")

    parser.add_argument("--out-ranking", type=str,
            help="Updated rankings to write to, used in certain analysis types")

    return parser


if __name__ == "__main__":
    args = make_parser().parse_args()

    results = load_csv(args.file)

    for i in range(len(ANALYSIS_TYPES)):
        if args.analysis_type == ANALYSIS_TYPES[i]:
            ANALYSIS_FUNCS[i](results, args)
