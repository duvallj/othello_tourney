import os
import sys
import importlib
from multiprocessing import Process, Value
import time
import socket

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
        importlib.invalidate_caches()
        os.chdir(path)

        sys.path = [path] + old_sys

        print(os.getcwd(), sys.path)
        sys.stdout.flush()
        # Why did this work earlier and not now?
        
        self.strat = importlib.import_module('private.Students.'+name+'.strategy').Strategy().best_strategy

        os.chdir(old_path)
        sys.path = old_sys

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

class AIManager:
    def __init__(self):
        self.used_ports = set()
        self.unused_ports = set(range(5000,6000))
        self.processes = list()
        self.rqsocket = socket.socket(socket.AF_INET6)
        self.rqsocket.bind(('', 9820))

    def mainloop(self):
        # This socket code is terrible b/c
        # it assumes networks are perfect, but
        # hey, it should work
        while True:
            self.rqsocket.listen(0)
            conn, addr = self.rqsocket.accept()

            for i in list(range(len(self.processes)))[::-1]:
                print(i)
                proc, port = self.processes[i]
                if not proc.is_alive():
                    proc.join()
                    self.unused_ports.add(port)
                    self.used_ports -= {port}
                    del self.processes[i]

            name = conn.recv(1024).decode()
            conn.send(bytes('OK', 'utf-8'))
            tml = conn.recv(128).decode()
            
            lai = LocalAI(name, tml)

            new_port = self.unused_ports.pop()
            self.used_ports.add(new_port)

            conn.send(bytes(str(new_port), 'utf-8'))
            
            new_sock = socket.socket(socket.AF_INET6)
            new_sock.bind(('', new_port))
            new_sock.listen(0)
            nconn, naddr = new_sock.accept()

            p = Process(target=self.serve_ai, args=(nconn, lai))
            p.start()
            self.processes.append((p, new_port))

    def serve_ai(self, conn, lai):
        message = ''
        while message != 'kys':
            message = ''
            while not message.endswith('\n'):
                message += conn.recv(1024).decode()
            message = message[:-1]
            if len(message) > 5:
                board, player = message.split(' ')
                move = lai.get_move(board, player)
                conn.send(bytes(str(move), 'utf-8'))
        

if __name__=="__main__":
    man = AIManager()
    print('mainlooping')
    man.mainloop()
