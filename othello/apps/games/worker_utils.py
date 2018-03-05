import os, sys
import importlib
    
def get_strat(name):
    old_path = os.getcwd()

    path = os.path.join(old_path, 'students/', name)
    new_path = path
    os.chdir(path)

    sys.path = [os.getcwd(), shared_dir] + ORIGINAL_SYS
    new_sys = sys.path[:]
    
    strat = importlib.import_module('students.'+name+'.strategy').\
            Strategy().best_strategy

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