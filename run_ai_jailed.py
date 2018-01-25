import os, sys
import logging as log
import io
import shlex, subprocess
import eventlet

from run_ai import AIBase, LocalAI
import Othello_Core as oc

# You'd think running a separate AI server in
# a VM locally would be enough, but we want to
# separate the AIs from each other when they run
# too, not allowing students to access other's code.

NAME_REPLACE = "{NAME}"

class JailedAIServer:
    AIClass = LocalAI
    def __init__(self, possible_names, *args, **kw):
        self.possible_names = possible_names
        
    def handle(self, client_in, client_out, client_err, sock):
        #####
        # Example: b"duv\n5\n@\n?????..??o@?????\n"
        #####
        
        name = client_in.readline().strip()
        if name not in self.possible_names:
            log.debug("Data not ok")
            client_out.write("-1"+"\n")
            return
        timelimit = client_in.readline().strip()
        player = client_in.readline().strip()
        board = client_in.readline().strip()
        log.debug("Got data {} {} {} {}".format(name, timelimit, player, board))

        eventlet.sleep(0)
        
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
            err = io.BytesIO()
            save_err = sys.stderr
            sys.stderr = err
            save_stdout = sys.stdout
            sys.stdout = io.BytesIO()
            
            strat = self.AIClass(name, possible_names)
            move, _ = strat.get_move(board, player, timelimit, False)
            # And then put it back where we found it
            sys.stdout = save_stdout
            sys.stderr = save_err
            
            log.debug("Got move {}".format(move))
            client_out.write(str(move)+"\n")
        else:
            log.debug("Data not ok")
            client_out.write("-1"+"\n")
        #client_out.flush()

    def run(self):
        self.handle(sys.stdin, sys.stdout, sys.stderr, None)

class JailedAI(AIBase):
    def __init__(self, *args, jail_begin='', **kw):
        super().__init__(*args, **kw)
        self.jail_begin = jail_begin

    def get_move(self, board, player, timelimit, kill_event):
        #####
        # Data format same as in RemoteAI,
        # b"duv\n5\n@\n?????..??o@?????\n"
        #####
        data = self.name+"\n"+str(timelimit)+"\n"+player+"\n"+str(board)+"\n"

        # Open subprocess
        command = self.jail_begin.replace(NAME_REPLACE, self.name)
        command_args = shlex.split(command)
        proc = subprocess.Popen(command_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.debug('Started subprocess with command '+str(command_args))
        outs, errs = proc.communicate(input=bytes(data, 'utf-8'))
        log.debug(errs.decode())
        log.debug('Got move from subprocess')
        try:
            move = int(outs.decode('utf-8').split("\n")[0])
        except:
            move = -1
        return move, errs.decode()

if __name__=="__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn')
    log.basicConfig(format='%(asctime)s:%(levelname)s:[JAILED]:%(message)s', level=log.DEBUG)
    student_folder = os.path.join(os.getcwd(), 'students')
    folders = os.listdir(student_folder)
    log.debug('Listed student folders successfully')
    possible_names =  {x for x in folders if \
        x != '__pycache__' and \
        os.path.isdir(os.path.join(student_folder, x))
    }
    JailedAIServer(possible_names).run()
        
        
