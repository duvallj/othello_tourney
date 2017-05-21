import os
import sys
import importlib
from multiprocessing import Process, Value
import time

from othello_admin import *

class LocalAI:
    def __init__(self, name, timelimit):
        self.name = name
        if timelimit.isdigit():
            self.timelimit = int(timelimit)
        else:
            self.timelimit = 5

        old_path = os.getcwd()
        old_sys = sys.path

        path = old_path + '/private/Students/'+name
        os.chdir(path)

        sys.path = [path] + old_sys

        self.strat = importlib.import_module('private.Students.'+name+'.strategy').\
                     Strategy().best_strategy

        os.chdir(old_path)
        sys.path = old_sys

    def get_move(self, board, player):
        best_shared = Value("i", -1)
        best_shared.value = 11
        running = Value("i", 1)
        p = Process(target=self.strat, args=(board, player, best_shared, running))
        p.start()
        t1 = time.time()
        p.join(self.timelimit)
        running.value = 0
        time.sleep(0.01)
        p.terminate()
        time.sleep(0.01)
        #handle = ctypes.windll.kernel32.OpenProcess(1, False, p.pid)
        #ctypes.windll.kernel32.TerminateProcess(handle, -1)
        #ctypes.windll.kernel32.CloseHandle(handle)
        if p.is_alive(): os.kill(p.pid, signal.SIGKILL)
        move = best_shared.value
        return move


if __name__=="__main__":
    ai = LocalAI(sys.argv[1], sys.argv[2])
    # That means we just got called by srun
    recv = ''
    while recv != 'kys':
        recv = sys.stdin.readline()[:-1]
        if recv == 'kys':
            break
        board, player = recv.split(' ')
        sys.stderr.write(str(ai.get_move(board, player)))
        sys.stderr.flush()
