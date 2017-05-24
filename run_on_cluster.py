#!/usr/bin/python3

import logging as log
import socket
import random

host_list = ['ovm1.vm.sites.tjhsst.edu']

class RemoteAI:
    def __init__(self, name):
        self.name = name
        self.host = random.choice(host_list)

    def make_connection(self, timelimit):
        if self.name == 'you':
            return

        self.socket = socket.socket(socket.AF_INET6)
        self.socket.connect((self.host,9820))

        self.socket.send(bytes(self.name, 'utf-8'))
        rcv = self.socket.recv(2)
        self.socket.send(bytes(str(timelimit), 'utf-8'))
        port = self.socket.recv(128).decode()
        port = int(port)

        self.socket.close()
        self.socket = socket.socket(socket.AF_INET6)
        self.socket.connect((self.host,port))

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

