import pickle
import csv
import os

AI = 'alphazero'

def fullpath(fname):
    return os.path.join('' if fname.startswith('/') else os.getcwd(), fname)

fname = input('Enter aztr filename: ')
if not os.path.isfile(fullpath(fname)):
    print("That's not a valid file!")
    fname = input('Enter aztr filename: ')

f = open(fullpath(fname), 'rb')

indata = pickle.load(f)
f.close()

data = dict()

for winner, board, players in indata:
    name, color = [(players[k], k) for k in players if players[k].startswith(AI)][0]
    iteration = name[len(AI):]
    data[iteration] = data.get(iteration, [])
    data[iteration].append((winner==color, board.count(color)))

ofname = fname + '.csv'
of = open(fullpath(ofname), 'w')
w = csv.DictWriter(of, ['iter', 'winpct', 'boardpct'])
w.writeheader()

for iteration in data:
    w.writerow({
        'iter': iteration,
        'winpct': sum(i[0] for i in data[iteration])/len(data[iteration]),
        'boardpct': sum(i[1] for i in data[iteration])/64/len(data[iteration]),
    })

of.close()
print("Done!")
