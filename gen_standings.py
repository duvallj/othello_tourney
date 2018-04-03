#!/usr/bin/python3
import random

random.seed(100)

game_output = "static/games/all/"
list_dir = "lists"
list_files = ("round_01.txt","round_02.txt")
forbidden_students = ("2019schawla", "2019cwiseman", "2019smohanty", "2018fawan","2019jduvall")

class StandingsItem:
    def __init__(self, name, score, tokens):
        self.name, self.score, self.tokens = name, score, tokens
        

def previous_games():
    prev_games = set()
    for j in list_files:
        file = open(list_dir + "/" + j, "r")
        data = [l.strip().split(",") for l in file.readlines()]
        data = {tuple(sorted(x)) for x in data}
        prev_games = prev_games.union(data)
        file.close()
    return prev_games

def tokenize(i):
    return abs(i) if abs(i)<100 else 0

def standings():
    file = open(game_output+"/results.txt", 'r')
    data = file.readlines()[:]
    data = [x.strip() for x in data if "20" in x]
    points = {}
    tokens = {}
    for line in data:
        b,w,s,*e = line.split(",")
        if not b in points.keys(): points[b],tokens[b]=0,0
        if not w in points.keys(): points[w],tokens[w]=0,0
        s = int(s)
        if s>0:
            points[b] += 1
            tokens[b] += tokenize(s)
            tokens[w] -= tokenize(s)
        elif s<0:
            points[w] += 1
            tokens[w] += tokenize(s)
            tokens[b] -= tokenize(s)
        else:
            points[b] += 0.5
            points[w] += 0.5
    standings = [StandingsItem(name, score, tokens[name])\
                 for name, score in points.items() \
                 if name not in forbidden_students]
    standings.sort(key = lambda x: (-x.score, -x.tokens))
    file.close()
    return standings


def get_pairing_from_standing(standings):
    standings.sort(key = lambda x: (-x.score, -x.tokens+20*random.random()))
    numwins = sorted(list({x.score for x in standings}), key=lambda x: -x)
    group = {}
    all_groups = []
    for w in numwins:
        group[w] = [p for p in standings if p.score == w]
        group[w].sort(key = lambda p: -p.tokens+5*random.random()) # shuffle to eliminate repeat games?
        print(w, len(group[w]))
        all_groups += [group[w]]
        
    for i in range(len(all_groups)-1):
        if len(all_groups[i]) % 2 == 1:
            print("fixing group %i" % i)
            all_groups[i].append(all_groups[i+1].pop())
        else:
            print("group %i is even length" % i)

    if len(all_groups[-1]) %2 == 1:
        randomplayer = StandingsItem("random", 0, 0)
        all_groups[-1].append(randomplayer)
        
    print([len(x) for x in all_groups])
    pairs = []
    for group in all_groups:
        l = len(group)
        these_pairs = list(zip(group[:l//2],group[l//2:]))
        pairs += these_pairs
    #pairs = zip(standings[0::2], standings[1::2])
    return list(pairs)


def check_conflicts(pairs, prev_games):
    for i,j in pairs:
    #    print(i.name,j.name)
        if tuple(sorted([i.name,j.name])) in prev_games:
            print("FAIL")
            print("FAILING:", i.name, j.name)
            return False
    #print("No Conflicts")
    return True


if __name__ == "__main__":
    prev_games = previous_games()
    stands = standings()
    conflicts = False
    while(not conflicts):
        pairs = get_pairing_from_standing(stands)
        conflicts = check_conflicts(pairs, prev_games)
    print("------------------------")
    for p1,p2 in pairs:
        print("%s,%s" % (p1.name, p2.name))
    print("------------------------")
    for p1,p2 in pairs:
        print("%s(%i,%i),%s(%i,%i)" % (p1.name, p1.score, p1.tokens, p2.name, p2.score, p2.tokens))


