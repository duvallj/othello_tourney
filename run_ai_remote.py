import eventlet
from eventlet.green import socket
import random
import logging as log

from run_ai import AIBase, LocalAI
import Othello_Core as oc

class LocalAIServer:
    def __init__(self, possible_names, AI_class=LocalAI):
        self.strats = dict()
        self.possible_names = possible_names
        for name in possible_names:
            self.strats[name] = AI_class(name, possible_names)
        
        self.should_continue = True

    def handle(self, client, sock):
        #####
        # Example: b"duv\n5\n@\n?????..??o@?????\n"
        #####
        
        name = client.readline().strip()
        timelimit = client.readline().strip()
        player = client.readline().strip()
        board = client.readline().strip()
        log.debug("Got data {} {} {} {}".format(name, timelimit, player, board))

        eventlet.sleep(0)
        
        if name in self.possible_names and \
           (player == oc.BLACK or player == oc.WHITE):

            try:
                timelimit = float(timelimit)
            except ValueError:
                timelimit = 5
            log.debug("Data is ok")
            move = self.strats[name].get_move(board, player, timelimit)
            log.debug("Got move {}".format(move))
            client.write(str(move)+"\n")
        else:
            log.debug("Data not ok")
            client.writeline("-1"+"\n")
        
        client.close()
        sock.close()

    def run(self, host, family):
        server = eventlet.listen(host, family)
        pool = eventlet.GreenPool(10000)
        while self.should_continue:
            client, address = server.accept()
            
            log.info("Accepted {}".format(address))
            pool.spawn_n(self.handle, client.makefile('rw'), client)
        

class RemoteAI(AIBase):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.remotes = self.extra
        assert bool(self.remotes)

    def get_move(self, board, player, timelimit):
        hostname, port = random.choice(self.remotes)
        addr = socket.getaddrinfo(hostname, port)
        host, family = addr[0][4], addr[0][0]
        log.debug("Target: {} {}".format(host, family))

        sock = socket.socket(family)
        sock.connect(host)

        data = "\n".join((self.name, str(timelimit), player, board))+"\n"
        log.debug("Sending data "+repr(data))
        sock.sendall(bytes(data, 'utf-8'))

        move = sock.recv(64).decode('utf-8')
        log.debug("Recieved move {}".format(move))
        try:
            move = int(move)
        except ValueError:
            move = -1
        return move
        
        
