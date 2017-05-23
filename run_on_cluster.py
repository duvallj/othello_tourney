#!/usr/bin/python3

import logging as log
import socket

class RemoteAI:
    def __init__(self, name):
        self.name = name

    def make_connection(self, timelimit):
        if self.name == 'you':
            return

        self.socket = socket.socket(socket.AF_INET6)
        self.socket.connect(('ovm1.vm.sites.tjhsst.edu',9820))

        self.socket.send(bytes(self.name, 'utf-8'))
        rcv = self.socket.recv(2)
        self.socket.send(bytes(str(timelimit), 'utf-8'))
        port = self.socket.recv(128).decode()
        port = int(port)

        self.socket.close()
        self.socket = socket.socket(socket.AF_INET6)
        self.socket.connect(('ovm1.vm.sites.tjhsst.edu',port))

    def get_move(self, board, player):
        if self.name == 'you':
            return -1

        self.socket.send(bytes(board+' '+player+'\n', 'utf-8'))
        result = self.socket.recv(4).decode()
        if result.isdigit():
            return int(result)
        else:
            return -1

    def kill_remote(self):
        if self.name == 'you':
            return

        self.socket.send(bytes('kys\n', 'utf-8'))
        self.socket.close()

#if __name__=='__main__':
#    ai = RemoteAI('strategy5_2019jduvall')
#    ai.make_connection(2)
#    import othello_admin as oa
#    print(ai.get_move(''.join(oa.Strategy().initial_board()), '@'))

