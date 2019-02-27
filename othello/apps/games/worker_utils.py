import os, sys
import importlib
from django.conf import settings

ORIGINAL_SYS = sys.path[:]

def get_strat(name):
    old_path = os.getcwd()

    stratargs = tuple()
    if name.startswith(settings.OTHELLO_AI_UNLIMITED_PLAYER):
        try:
            stratargs = (int(name[len(settings.OTHELLO_AI_UNLIMITED_PLAYER):]),)
        except:
            pass
        name = settings.OTHELLO_AI_UNLIMITED_PLAYER
    
    path = os.path.join(old_path, 'students/', name)
    new_path = path
    os.chdir(path)

    sys.path = [os.getcwd(), settings.OTHELLO_AI_SHARED_DIR] + ORIGINAL_SYS
    new_sys = sys.path[:]

    strat = importlib.import_module('students.'+name+'.strategy').\
            Strategy(*stratargs).best_strategy

    os.chdir(old_path)
    sys.path = ORIGINAL_SYS

    return strat, new_path, new_sys

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
