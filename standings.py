class StandingsItem:
    def __init__(self, name, score):
        self.name, self.score = name, score

dir = "static/games/all"
file = open(dir+"/results.txt", 'r')
data = file.readlines()[:]
data = [x.strip() for x in data if "20" in x]
points = {}
for line in data:
    b,w,s,*e = line.split(",")
    if not b in points.keys(): points[b]=0
    if not w in points.keys(): points[w]=0

    s = int(s)
    if b == "2019isethi": print(b,"b",points[b],s, line )
    if w == "2019isethi": print(w,"w",points[w],s, line )
    if s>0:
        points[b] += 1
        if b=="2019isethi": print("incrementing isethi")
    elif s<0:
        points[w] += 1
        if w=="2019isethi": print("incrementing isethi")
    else:
        points[b] += 0.5
        points[w] += 0.5
standings = [StandingsItem(name, score) for name, score in points.items()]
standings.sort(key = lambda x: (-x.score, x.name))
file.close()

    
