import os
import sys
import subprocess
import argparse

from run_ai import AIBase, LocalAI

parser = argparse.ArgumentParser(description="Run an AI inside a jail, communicating only in stdin and stdout.")
parser.add_argument('--jail_begin', type=str, default="",
                    help="Command to run a process jailed.")
parser.add_argument('ai', type=str,
                    help="Name of AI to run jailed")

class LocalAIWrapper:
    pass

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
        
        
