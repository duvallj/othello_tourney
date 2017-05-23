#!/usr/bin/python3

import logging as log
import socket

class RemoteAI:
    def __init__(self, name):
        self.name = name

    def make_connection(self, timelimit):
        self.socket = socket.socket()
        self.socket.connect(('localhost',9820))

        self.socket.send(bytes(self.name, 'utf-8'))
        rcv = self.socket.recv(2)
        self.socket.send(bytes(str(timelimit), 'utf-8'))
        port = self.socket.recv(128).decode()
        port = int(port)

        self.socket.close()
        self.socket = socket.socket()
        self.socket.connect(('localhost',port))

    def get_move(self, board, player):
        self.socket.send(bytes(board+' '+player+'\n', 'utf-8'))
        result = self.socket.recv(4).decode()
        if result.isdigit():
            return int(result)
        else:
            return -1

    def kill_remote(self):
        self.socket.send(bytes('kys\n', 'utf-8'))
        self.socket.close()

