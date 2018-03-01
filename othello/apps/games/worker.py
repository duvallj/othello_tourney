from django.conf import settings
import logging as log
import sys, os, io
import shlex, traceback

"""
Plan:
use django channel consumer for bg process
have that consumer use this runner to create 2 long running jailed processes beside it
this class will take consumer as an arg in order to send channel api messages
"""

class GameRunner:
    pass
    
    
class JailedRunner:
    """
    The class that is run in the subprocess to handle the games
    Keeps running until it is killed forcefully
    """
    def __init__(self, *args, **kwargs):
        # I don't know what to put here yet
        pass
    
    def handle(self, client_in, client_out, client_err):
        """
        Handles one incoming request for getting a move from the target AI
        given the current board, player to move, and time limit.
        
        client_in, client_out, and client_err are socket-like objects.
        input received on client_in, output sent out on client_out, any 
        errors the AI throws are sent on client_err
        """
        name = client_in.readline().strip()
        timelimit = client_in.readline().strip()
        player = client_in.readline().strip()
        board = client_in.readline().strip()
        log.debug("Got data {} {} {} {}".format(name, timelimit, player, board))
        
        if name in self.possible_names and \
           (player == oc.BLACK or player == oc.WHITE):

            try:
                timelimit = float(timelimit)
            except ValueError:
                timelimit = 5
            log.debug("Data is ok")
            # Now, we don't want any debug statements
            # messing up the output. So, we replace
            # sys.stdout temporarily
            
            #save_err = sys.stderr
            #sys.stderr = io.BytesIO()
            save_stdout = sys.stdout
            sys.stdout = io.TextIOWrapper(io.BytesIO())
            
            strat = self.AIClass(name, possible_names)
            move, err = strat.get_move(board, player, timelimit, False)
            
            # And then put stdout back where we found it
            sys.stdout = save_stdout
            #sys.stderr = save_err
            if err is not None: client_err.write(err)
            
            log.debug("Got move {}".format(move))
            client_out.write(str(move)+"\n")
        else:
            log.debug("Data not ok")
            client_out.write("-1"+"\n")
        client_out.flush()
        client_err.flush()
        
    def run(self):
        while True:
            self.handle(sys.stdin, sys.stdout, sys.stderr)
            
class JailedRunnerCommunicator:
    """
    Class used to communicate with a jailed process.
    
    Standard usage:
    ai = JailedRunnerCommunicator(ai_name)
    ai.start()
    ...
    move, errors = ai.get_move(board, player, timelimit)
    if core.is_legal(board, move): core.make_flips(board, move)
    ...
    ai.stop()
    """
    def __init__(self, ai_name):
        self.name = ai_name
        self.proc = None
        
    def start(self):
        """
        Starts running the specified AI in a subprocess
        """
        command = settings.OTHELLO_AI_RUN_COMMAND.replace(settings.OTHELLO_AI_NAME_REPLACE, self.name)
        command_args = shlex.split(command)
        self.proc = subprocess.Popen(command_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, \
                                    universal_newlines=True, bufsize=1, cwd=settings.PROJECT_ROOT)

    def get_move(self, board, player, timelimit):
        """
        Gets a move from the running subprocess, providing it with all the data it
        needs to make a decision.
        
        Data format needs to be same as JailedRunner expects it, namely,
        b"duv\n5\n@\n?????..??o@?????\n"
        """
        data = self.name+"\n"+str(timelimit)+"\n"+player+"\n"+str(board)+"\n"

        log.debug('Started subprocess')
        self.proc.stdin.write(data.encode('utf-8'))
        self.proc.stdin.flush()
        outs = self.proc.stdout.readline()
        errs = self.proc.stderr.read()
        log.debug('Got move from subprocess')
        try:
            move = int(outs.decode('utf-8').split("\n")[0])
        except:
            traceback.print_exc()
            move = -1
        return move, errs.decode()
        
    def stop(self):
        """
        Stops the currently running subprocess.
        Will throw an error if the subprocess is not running.
        """
        self.proc.kill()
        self.proc = None
        
    def __del__(self):
        self.stop()
        super().__del__()