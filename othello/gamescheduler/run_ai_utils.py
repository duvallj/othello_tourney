import logging
import sys, os, io
import shlex, traceback
from threading import Event
from queue import Empty
import multiprocessing as mp
import subprocess
import time
import signal

from .settings import OTHELLO_AI_RUN_COMMAND, OTHELLO_AI_NAME_REPLACE, OTHELLO_AI_MAX_TIME
from .settings import PROJECT_ROOT
from .utils import get_strat, get_stream_queue, safe_int
from .othello_admin import Strategy
from .othello_core import BLACK, WHITE, EMPTY

ORIGINAL_SYS = sys.path[:]

log = logging.getLogger(__name__)


class HiddenPrints:
    """
    Surpresses all stdout from a subprocess so we
    can only send what we need to to our parent
    """
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = sys.stderr

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout

class LocalRunner:
    def __init__(self, ai_name):
        self.name = ai_name
        self.strat = None
        self.new_path = self.old_path = os.getcwd()
        self.new_sys = self.old_sys = ORIGINAL_SYS
        try:
            self.strat, self.new_path, self.new_sys = get_strat(self.name)
        except:
            log.warn("LocalRunner threw exception when importing {}. Traceback below".format(ai_name))
            traceback.print_exc()
            self.strat = None

    def strat_wrapper(self, board, player, best_shared, running, pipe_to_parent):
        with HiddenPrints():
            try:
                best_shared.value = -6
                self.strat(board, player, best_shared, running)
                pipe_to_parent.send(None)
            except:
                pipe_to_parent.send(traceback.format_exc())

    def get_move(self, board, player, timelimit):
        """
        Starts a multiprocessing.Process with the student AI inside,
        automatically kills it after the timelimit expires

        Different negative numbers used for debugging purposes, to know exactly
        where it fails
        """
        if self.strat is None:
            return -5, "Failed to load Strategy"

        best_shared = mp.Value("i", -7)
        running = mp.Value("i", 1)

        os.chdir(self.new_path)
        sys.path = self.new_sys
        to_child, to_self = mp.Pipe()
        p = None
        try:
            p = mp.Process(
                target = self.strat_wrapper,
                args = (
                    "".join(list(board)),
                    player,
                    best_shared,
                    running,
                    to_child
                )
            )
            p.start()
            p.join(timelimit)

            move = -9
            err = None

            # Join with a timelimit doesn't mean that the process has ended yet
            if p.is_alive():
                # Notify process that it is about to be killed
                running.value = 0
                p.join(0.05)
                # We need to read from shared value and pipe **before** killing
                # the process because otherwise the subprocess could be
                # holding a lock on one of them and deadlock this process
                move = best_shared.value
                if to_self.poll():
                    err = to_self.recv()
                    log.info("LocalRunner caught threwn error")
                else:
                    err = None
                    log.debug("LocalRunner did not throw an error")

                # If the subprocess was still alive, kill it fully
                if p.is_alive():
                    p.terminate()
                    # Should be instantaneous now that process is killed... I hope
                    p.join()
                    p = None
            else:
                # No need to worry about any deadlocks or stuff, just
                # read move and error as normal
                move = best_shared.value
                if to_self.poll():
                    err = to_self.recv()
                    log.info("LocalRunner caught threwn error")
                else:
                    err = None
                    log.debug("LocalRunner did not throw an error")

            return move, err

        except:
            traceback.print_exc()
            return -8, 'Server Error'
        finally:
            # Kill process even if something crazy happens
            # And yes, this is called even when we `return` above
            if not (p is None):
                p.terminate()
                p.join()
                p = None
            os.chdir(self.old_path)
            sys.path = self.old_sys


class JailedRunner:
    """
    The class that is run in the subprocess to handle the games
    UPDATE: needs to be told to quit so that all processes are cleaned up
    """

    # just in case some doofus wants to do distributed AI running instead
    AIClass = LocalRunner
    def __init__(self, ai_name):
        self.strat = self.AIClass(ai_name)
        self.name = ai_name
        self.running = False

    def handle(self, client_in, client_out, client_err):
        """
        Handles one incoming request for getting a move from the target AI
        given the current board, player to move, and time limit.

        client_in, client_out, and client_err are socket-like objects.
        input received on client_in, output sent out on client_out, any
        errors the AI throws are sent on client_err

        Expects one line containing the command, other lines should be sent
        as the command requires.
        """
        command = client_in.readline().strip()
        if command == "get_move":
            self.get_move(client_in, client_out, client_err)
        elif command == "stop":
            self.running = False
        else:
            log.info("Unknown command \"{}\"".format(command))

    def get_move(self, client_in, client_out, client_err):
        """
        Receives data of what moves to make, then prints out the move
        """
        name = client_in.readline().strip()
        timelimit = client_in.readline().strip()
        player = client_in.readline().strip()
        board = client_in.readline().strip()
        log.debug("Got data {} {} {} {}".format(name, timelimit, player, board))

        if name == self.name and \
           (player == BLACK or player == WHITE):

            try:
                timelimit = float(timelimit)
            except ValueError:
                timelimit = 5
            log.debug("Data is ok")
            # We don't want any debug statements messing up the output. 
            # So, we replace sys.stdout with sys.stderr temporarily
            with HiddenPrints():
                move, err = self.strat.get_move(board, player, timelimit)

            if not (err is None):
                client_err.write(err)

            log.debug("Got move {}".format(move))
            client_out.write("{}\n".format(move))
        else:
            log.debug("Data not ok")
            client_out.write("-1\n")
        client_out.flush()
        client_err.flush()

    def run(self):
        self.running = True
        while self.running:
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
        log.debug("JailedRunnerCommunicator created")

    def start(self):
        """
        Starts running the specified AI in a subprocess
        """
        log.debug("JailedRunnerCommunicator started")
        command = OTHELLO_AI_RUN_COMMAND.replace(OTHELLO_AI_NAME_REPLACE, self.name)
        command_args = shlex.split(command, posix=False)
        log.debug(command_args)
        self.proc = subprocess.Popen(command_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, \
                                    bufsize=1, universal_newlines=True, cwd=PROJECT_ROOT)
        self.stop_event = Event()
        self.proc_stdout = get_stream_queue(self.proc.stdout, self.stop_event)
        self.proc_stderr = get_stream_queue(self.proc.stderr, self.stop_event)

    def get_move(self, board, player, timelimit):
        """
        Gets a move from the running subprocess, providing it with all the data it
        needs to make a decision.

        Data format needs to be same as JailedRunner expects it, namely,
        b"duv\n5\n@\n?????..??o@?????\n"
        """
        data = self.name+"\n"+str(timelimit)+"\n"+player+"\n"+''.join(board)+"\n"

        log.debug('About to send {} to subprocess'.format(repr(data)))
        """
        x = "Debug:"
        while x:
            print(x)
            x = self.proc_stderr.get_nowait()
        """
        last_err_line = ""
        errs = []
        while last_err_line is not None:
            errs.append(last_err_line)
            try:
                last_err_line = self.proc_stderr.get_nowait()
            except:
                last_err_line = None
        errs = "".join(errs)
        if errs: log.error(errs)
        self.proc.stdin.write(data)
        self.proc.stdin.flush()
        log.debug("Done writing data")

        # this needs to be .get() in order to block until queue has something,
        # i.e. process is finished. Trusting JailedRunner to always output, but
        # just in case, actually do time out
        outs = ""
        try:
            outs = self.proc_stdout.get(timeout=timelimit+10)
        except Empty:
            log.warn("Timed out reading from subprocess!")

        log.debug("Got output, reading errors")
        errs2 = []
        last_err_line = ""
        while last_err_line is not None:
            errs2.append(last_err_line)
            try:
                last_err_line = self.proc_stderr.get_nowait()
            except:
                last_err_line = None
        errs += "".join(errs2)
        log.debug('Got full report from subprocess')
        move = safe_int(outs.split("\n")[0])
        return move, errs #.decode()

    def stop(self):
        """
        Stops the currently running subprocess.
        """
        if not (self.proc is None):
            self.proc.kill()
            self.stop_event.set()
            self.proc = None

    def __del__(self):
        # Just in case wonkiness
        self.stop()
