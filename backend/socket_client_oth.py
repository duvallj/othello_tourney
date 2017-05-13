### code based on
### https://shakeelosmani.wordpress.com/2015/04/13/python-3-socket-programming-example/

import socket
from othello_admin import *
import sys
import time
#from compute_standings import *
from random import choice

admin = None
board = None

known_hosts = ["gameandwatch", "donkeykong", "captainfalcon", "yoshi", "sonic", "metaknight", "kirby",
               "lucario", "peach", "torvalds", "thompson", "stallman", "kleinrock"]
connect_retry = 0


def human(board, player):
    """ Asks a human for input and returns the move. No error checking. """
    move = int(input("Your move, (1-9)" + str(player) + ":")) - 1
    return move


def ai_server(board, player, sockets):
    message = "%s %s" % (''.join(board), player)
    #print("CLIENT: sending %s:%s" % (sockets[player].getpeername(), player))
    sockets[player].sendall(message.encode())
    data = sockets[player].recv(1024).decode()
    move = int(data)
    #print("CLIENT: receivd %s:%s" % (sockets[player].getpeername(), data))
    return move


def end_game(sockets, portA, portB):
    message = "GAMEOVER"
    for s, t in zip(sockets, (portA, portB)):
        print("Client SENDING GAMEOVER to %i" % t)
        sockets[s].sendall(message.encode())


def connect_to_sockets(portA, portB):
    global host
    global connect_retry
    connect_retry += 1
    socketA = socket.socket()
    #print("CLIENT: Connecting to %s:%i" % (host, portA))
    try:
        socketA.connect(('localhost', portA))
    except ConnectionRefusedError:
        #print("CLIENT error. unable to connect to %s:%i" % (host, portA))
        if connect_retry > 20:
            #print("TERMINATED: (%2i:%i(B), %i(W)). Unable to connect" % (division, portA, portB))
            sys.exit()
        host = random.choice(known_hosts)
        #print("CLIENT error. Retying with host %s" % host)
        return connect_to_sockets(portA, portB)
    #print("CLIENT: Success")
    socketB = socket.socket()
    #print("CLIENT: Connecting to %s:%i" % (host, portB))
    try:
        socketB.connect(('localhost', portB))
    except ConnectionRefusedError:
        #print("CLIENT error. unable to connect to %s:%i" % (host, portB))
        if connect_retry > 20:
            #print("TERMINATED: (%2i:%i(B), %i(W)). Unable to connect" % (division, portA, portB))
            sys.exit()
        host = random.choice(known_hosts)
        #print("CLIENT error. Retying with host %s" % host)
        return connect_to_sockets(portA, portB)
    #print("CLIENT: Success")
    return (socketA, socketB)


def init_game():
    global admin
    global board

    admin = Strategy()
    board = admin.initial_board()


def play_single_game(portA, portB):
    global admin, board

    silent = True
    (socketA, socketB) = connect_to_sockets(portA, portB)

    sockets = {core.BLACK: socketA, core.WHITE: socketB}
    player = core.BLACK

    strategy_X = ai_server
    strategy_O = ai_server

    current_strategy = {core.BLACK: strategy_X, core.WHITE: strategy_O}
    # admin.print_board(board)

    forfeit = False
    # print("%i, %i, " %(portA, portB), end="")
    #out = open("/afs/csl.tjhsst.edu/staff/pewhite/oth/round1/games/%i_%i_%s.txt" % (
    #           portA, portB, time.strftime("%Y.%M.%d:%H.%M.%S")), "w")
    out = open("tmp.txt","w")
    while player is not None and not forfeit:
        move = current_strategy[player](board, player, sockets)
        if not admin.is_legal(move, player, board):
            print("CLIENT: %i vs %i: %s makes illegal move %i, forfeits" % (portA, portB, player, move))
            print(player, move)
            print("ILLEGAL MOVE, Forfeit by ", player, file=out)
            forfeit = True
            if player == core.BLACK:
                black_score = -100
            else:
                black_score = 100
            continue
        board = admin.make_move(move, player, board)
        print(player, move, file=out)
        print(admin.print_board(board), file=out)
        out.flush()
        player = admin.next_player(board, player)
        black_score = admin.score(core.BLACK, board)
    print("FINISHED: (%i(B), %i(W)). Black Score %i" % (portA, portB, black_score))
    print("FINISHED: (%i(B), %i(W)). Black Score %i" % (portA, portB, black_score), file=out)
    out.close()

    if black_score > 0:
        winner = portA
        loser = portB
        tie1 = 0
        tie2 = 0
    elif black_score < 0:
        winner = portB
        loser = portA
        tie1 = 0
        tie2 = 0
    else:
        winner = 0
        loser = 0
        tie1 = portA
        tie2 = portB
    outfile = open("round_1_results.txt", "a")
    print("%12s\t%2i\t%4i\t%4i\t%4i\t%4i\t%4i\t%s" % (host, division, winner, loser, tie1, tie2,
                                                      black_score, time.strftime("%c")), file=outfile)
    outfile.flush()
    outfile.close()
    # print(black_score)


    if black_score > 0:
        winner = socketA.getpeername()
    elif black_score < 0:
        winner = socketB.getpeername()
    else:
        winner = "TIE"

    end_game(sockets, portA, portB)

    for s in sockets.values():
        s.close()

    return (winner)


def play_three_games(portA, portB):
    (socketA, socketB) = connect_to_sockets(portA, portB)
    s1 = play_single_game(socketA, socketB)
    s2 = play_single_game(socketB, socketA)
    if (s1 == s2 and s1 != "TIE"):
        return (s1, s2, 0)
    else:
        if random.random() > 0.5:
            s3 = play_single_game(socketA, socketB)
        else:
            s3 = play_single_game(socketB, socketA)
    return (s1, s2, s3)


if __name__ == '__main__':
    global host
    global division

    port1 = 5000#int(sys.argv[1])
    port2 = 5001#int(sys.argv[2])
    division = 1#int(sys.argv[3])
    if len(sys.argv) > 4:
        host = sys.argv[4]
    else:
        host = "localhost"
    init_game()
    play_single_game(port1, port2)
#    update_standings()
