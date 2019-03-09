import os, sys
from threading import Thread
from queue import Queue, Empty
import importlib
import random
import string

from .settings import OTHELLO_STUDENT_PATH, OTHELLO_PUBLIC_PATH

ORIGINAL_SYS = sys.path[:]

def enqueue_stream_helper(stream, q):
    """
    Continuously reads from stream and puts any results into
    the queue `q`
    """
    for line in iter(stream.readline, b''):
        q.put(line)
    stream.close()

def get_stream_queue(stream):
    """
    Takes in a stream, and returns a Queue that will return the output from that stream. Starts a background thread as a side effect.
    """
    q = Queue()
    t = Thread(target=enqueue_stream_helper, args=(stream, q))
    t.daemon = True # Dies with the main program
    t.start()

    return q

def get_strat(name):
    old_path = os.getcwd()
    path = os.path.join(OTHELLO_STUDENT_PATH, name)
    new_path = path

    # actually go to new location so that import works right
    os.chdir(path)
    sys.path = [os.getcwd(), OTHELLO_PUBLIC_PATH] + ORIGINAL_SYS
    new_sys = sys.path[:]

    strat = importlib.import_module('students.'+name+'.strategy').\
            Strategy().best_strategy

    # restore previous state as to not mess up other code
    os.chdir(old_path)
    sys.path = ORIGINAL_SYS

    return strat, new_path, new_sys

def get_possible_strats():
    folders = os.listdir(OTHELLO_STUDENT_PATH)
    possible_names =  {x for x in folders if \
        x != '__pycache__' and \
        os.path.isdir(os.path.join(OTHELLO_STUDENT_PATH, x))
    }
    return possible_names

def generate_id(size=10, chars=string.ascii_letters + string.digits):
    return 'abc'
    #return ''.join(random.choice(chars) for _ in range(size))

def safe_int(s):
    try:
        return int(s)
    except:
        return -1

def safe_float(s):
    try:
        return float(s)
    except:
        return 5.0
