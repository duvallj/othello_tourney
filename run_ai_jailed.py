import os, sys
import logging
import time


from othello.gamescheduler.run_ai_utils import JailedRunner
from othello.gamescheduler.settings import OTHELLO_STUDENT_PATH

log = logging.getLogger(__name__)

if __name__=="__main__":
    log.basicConfig(format='%(asctime)s:%(levelname)s:[JAILED]:%(message)s', level=log.WARN)

    handler = logging.FileHandler(os.path.join(OTHELLO_STUDENT_PATH, time.strftime("log-%Y-%m-%d-%H-%M-%S.log")))
    handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:[JAILED]:%(message)s"))
    log.addHandler(handler)
    logger.setLevel(logging.INFO)

    JailedRunner(sys.argv[-1]).run()
