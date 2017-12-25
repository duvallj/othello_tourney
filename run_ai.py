import os
import sys
if sys.platform == 'win32' or sys.platform == 'cygwin':
    import ctypes
import importlib
from multiprocessing import Process, Value
import time
import socket

from othello_admin import *

sys.path = [sys.path[0]]+sys.path

class AIBase:
    def __init__(self, name, possible_names, extra=None):
        self.name = name
        self.possible_names = possible_names
        self.extra = extra

    def get_move(self, board, player, timelimit):
        return -1

def get_strat(name):
    old_path = os.getcwd()
    old_sys = sys.path[1:]

    path = old_path + '/private/Students/'+name
    os.chdir(path)

    sys.path = [os.getcwd()] + old_sys
    
    strat = importlib.import_module('private.Students.'+name+'.strategy').\
            Strategy().best_strategy

    os.chdir(old_path)
    #sys.path = old_sys

    return strat

class LocalAI(AIBase):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.strat = self.extra

        if self.strat is None and self.name in self.possible_names:
            self.strat = get_strat(self.name)
            

    def get_move(self, board, player, timelimit):
        best_shared = Value("i", -1)
        best_shared.value = 11

        running = Value("i", 1)

        p = Process(target=self.strat, args=(list(board), player, best_shared, running))
        p.start()

        t1 = time.time()

        p.join(timelimit)

        running.value = 0
        time.sleep(0.01)

        p.terminate()
        time.sleep(0.01)

        if sys.platform == 'win32' or sys.platform == 'cygwin':
            handle = ctypes.windll.kernel32.OpenProcess(1, False, p.pid)
            ctypes.windll.kernel32.TerminateProcess(handle, -1)
            ctypes.windll.kernel32.CloseHandle(handle)
        else:
            if p.is_alive(): os.kill(p.pid, 9)

        move = best_shared.value
        return move
