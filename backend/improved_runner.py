import socket_client_oth as sco
from othello_admin import *

def play_game(portA, portB, conn):
    admin = Strategy()
    
    socketA, socketB = sco.connect_to_sockets(portA, portB)
    sockets = {core.BLACK:socketA, core.WHITE:socketB}

    player = core.BLACK
    board = admin.initial_board()

    forfeit = False

    while player is not None and not forfeit:
        move = sco.ai_server(board, player, sockets)
        if not admin.is_legal(move, player, board):
            forfeit = True
            if player == core.BLACK:
                black_score = -100
            else:
                black_score = 100
            continue
        board = admin.make_move(move, player, board)
        player = admin.next_player(board, player)
        black_score = admin.score(core.BLACK, board)

        conn.send({'bSize':'8','board':''.join(board).replace('?',''), 'black':str(portA), 'white':str(portB)})
