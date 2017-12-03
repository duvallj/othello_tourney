import os
import sys
import importlib
from multiprocessing import Process, Value
import time
import socket

from othello_admin import *

sys.path = [sys.path[0]]+sys.path

class LocalAI:
    def __init__(self, name, possible_names, timelimit):
        self.name = name
        self.timelimit = timelimit

        if name in possible_names:
            old_path = os.getcwd()
            old_sys = sys.path[1:]

            path = old_path + '/private/Students/'+name
            os.chdir(path)

            sys.path = [os.getcwd()] + old_sys
            
            self.strat = importlib.import_module('private.Students.'+name+'.strategy').Strategy().best_strategy

            os.chdir(old_path)
            #sys.path = old_sys

    def get_move(self, board, player):
        best_shared = Value("i", -1)
        best_shared.value = 11
        running = Value("i", 1)
        p = Process(target=self.strat, args=(list(board), player, best_shared, running))
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
        if p.is_alive(): os.kill(p.pid, 9)
        move = best_shared.value
        return move
