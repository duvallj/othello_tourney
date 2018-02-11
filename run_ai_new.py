from importlib import import_module
from multiprocessing import get_context, TimeoutError
import traceback
import logging
# This is just for testing I guess
from sys import argv

logger = logging.Logger(__name__)

mp = get_context("spawn")

class TimeoutProcess:
    def __init__(self, timeout, target, args):
        self.timeout = timeout
        self.func = target
        self.to_pass = args

    def run(self):
        with mp.Pool(1) as pool:
            result = pool.apply_async(self.func, self.to_pass)
            try:
                result.get(timeout=self.timeout)
            except TimeoutError:
                pass
            except Exception:
                return traceback.format_exc()

class AI:
    def __init__(self, name, **kwargs):
        self.strategy = import_module('students.{}.strategy'.format(name)).Strategy()

    def get_move(self, board, player, timeout):
        best = mp.Manager().Value("i", -1)
        ret = TimeoutProcess(timeout, target=self.strategy.best_strategy, args=(list(board), player, best)).run()
        return ret if ret else best.value

if __name__ == "__main__":
    a = AI(argv[1])
    ret = a.get_move('???????????........??........??........??...o@...??...@o...??........??........??........???????????', '@', float(argv[2]))
    print(ret)
