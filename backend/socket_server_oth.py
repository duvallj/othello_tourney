#!/usr/bin/python3
### code based on from
### https://shakeelosmani.wordpress.com/2015/04/13/python-3-socket-programming-example/

TIMELIMIT = 1

import socket
# import students.strategy2_2019agorle as ai
# import strategy as ai
import sys
import importlib
import logging
from multiprocessing import Value, Process
import time
import os, signal
import argparse

logging.basicConfig(filename='server_%s.log' % socket.gethostname(), level=logging.DEBUG)


def get_move(strategy, board, player, time_limit):
    best_shared = Value("i", -1)
    best_shared.value = 11
    running = Value("i", 1)
    p = Process(target=strategy, args=(board, player, best_shared, running))
    p.start()
    t1 = time.time()
    p.join(time_limit)
    running.value = 0
    time.sleep(0.01)
    p.terminate()
    time.sleep(0.01)
    if p.is_alive(): os.kill(p.pid, signal.SIGKILL)
    move = best_shared.value
    return move


def Main(strat_lib, host, port):
    old_sys = sys.path
    project_dir = os.getcwd()
    student_dir = "Students"
    (t1, n, t2) = strat_lib.split(".")

    strategy_folder_name = n
    student_path = project_dir + "/" + student_dir + "/" + strategy_folder_name

    sys.path = [student_path] + old_sys
    os.chdir(student_path)
    # print("cd to %s", student_path)
    # print(sys.path)

    print("-" * 50)
    print("importing", n)
    # host = socket.gethostname()
    ai = importlib.import_module(strat_lib)
    STRATEGY = ai.Strategy().best_strategy

    mySocket = socket.socket()
    mySocket.bind(('', port)) # listen to any host
    logging.info(time.strftime("%Y.%M.%d:%H.%M.%S")+":Binding %s to %i with lib %s", socket.gethostname(), port, strat_lib)
    
    while True:
        mySocket.listen()
        conn, addr = mySocket.accept()
        logging.info("SERVER on port %i accepted conenction from %s " % (port, str(addr)))
        while True:
            data = conn.recv(1024).decode()
            logging.info(time.strftime("%Y.%M.%d:%H.%M.%S")+":RCVD Port %i: %s " % (port, str(data)))
            if len(data)<3:
                logging.info(time.strftime("%Y.%M.%d:%H.%M.%S")+":Improper transmittion, SERVER ENDING GAME %i" % port)
                conn.close()
                break
            if data[:8]=="GAMEOVER":
                logging.info(time.strftime("%Y.%M.%d:%H.%M.%S")+":SERVER ENDING GAME %i" % port)
                conn.close()
                break
            if (len(data) >= 5):
                (board_str, player) = data.split()
                board = list(board_str)
                # move = STRATEGY(board, player)
                move = get_move(STRATEGY, board, player, time_limit=TIMELIMIT)
                data = str(move) + "\n"
                logging.info(time.strftime("%Y.%M.%d:%H.%M.%S")+"SEND Port %i Sending move: %i, player %s" % (port, move, player))
                conn.send(data.encode())

    #outfile.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start up Othello'
                                                 'Servers')
    parser.add_argument('-f', '--file', help='Python class file to load', required=True)
    parser.add_argument('-p', '--port', help='Port to run service on', required=True)
    parser.add_argument('-s', '--server', help='IP4 address to listen to, ignored!', required=True)
    args = parser.parse_args()

    Main(args.file, args.server, int(args.port))
    input()
