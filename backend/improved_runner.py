from othello_admin import *
import os
import time
import ctypes

TIMELIMIT = 5

def get_move(strategy, board, player, time_limit):
    best_shared = mp.Value("i", -1)
    best_shared.value = 11
    running = Value("i", 1)
    p = np.Process(target=strategy, args=(board, player, best_shared, running))
    p.start()
    t1 = time.time()
    p.join(time_limit)
    running.value = 0
    time.sleep(0.01)
    p.terminate()
    time.sleep(0.01)
    handle = ctypes.windll.kernel32.OpenProcess(1, False, p.pid)
    ctypes.windll.kernel32.TerminateProcess(handle, -1)
    ctypes.windll.kernel32.CloseHandle(handle)
    #if p.is_alive(): os.kill(p.pid, signal.SIGKILL)
    move = best_shared.value
    return move
    

def play_game(nameA, nameB, conn, name2strat):
    admin = Strategy()
    
    strategy = {core.BLACK:name2strat[nameA], core.WHITE:name2strat[nameB]}
    names ={core.BLACK:nameA, core.WHITE:nameB}

    player = core.BLACK
    board = admin.initial_board()

    forfeit = False

    while player is not None and not forfeit:
        if names[player] == 'you':
            pass
        else:
            move = get_move(strategy[player], board, player, TIMELIMIT)
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

        conn.send({'bSize':'8',
                   'board':''.join(board).replace('?',''),
                   'black':nameA,
                   'white':nameB,
                   'tomove':admin.opponent(player)})
