import os, sys
import logging
import time


from othello.gamescheduler.run_ai_utils import JailedRunner
from othello.gamescheduler.settings import OTHELLO_STUDENT_PATH

log = logging.getLogger(__name__)

if __name__=="__main__":
    logging.basicConfig(format='%(asctime)s:%(levelname)s:[JAILED]:%(message)s', level=logging.DEBUG)

    handler = logging.FileHandler(os.path.join(OTHELLO_STUDENT_PATH, sys.argv[-1], time.strftime("log-%Y-%m-%d-%H-%M-%S.log")))
    handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:[JAILED]:%(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    JailedRunner(sys.argv[-1]).run()
