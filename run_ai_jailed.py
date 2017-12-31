import os
import sys
import subprocess

from run_ai import AIBase, LocalAI
from run_ai_remote import LocalAIServer

# Turns out we don't really need this...
# Having separate VM or LXC servers handling the
# requests w/ the things in run_ai_remote is enough.

class JailedAIServer(LocalAIServer):
    def __init__(self, possible_names, AI_class=LocalAI):
        super().__init__(possible_names, AI_class)

    def cleanup(self, client_in, client_out, sock):
        pass

    def run(self):
        self.handle(sys.stdin, sys.stdout, None)

class JailedAI(AIBase):
    def __init__(self, *args, jail_begin='', **kw):
        super().__init__(*args, **kw)
        self.jail_begin = jail_begin

    def get_move(self, board, player, timelimit):
        #####
        # Data format same as in RemoteAI,
        # b"duv\n5\n@\n?????..??o@?????\n"
        #####
        data = self.name+"\n"+str(timelimit)+"\n"player+"\n"+board+"\n"

        # Open subprocess
        # Send data to subprocess
        # Get data from subprocess

if __name__=="__main__":
    JailedAIServer().run()
        
        
