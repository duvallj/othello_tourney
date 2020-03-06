import os, sys
import logging
import time


from othello.gamescheduler.run_ai_utils import JailedRunner
from othello.gamescheduler.settings import OTHELLO_STUDENT_PATH

log = logging.getLogger(__name__)

if __name__=="__main__":
    root_logger = logging.getLogger(None)
    root_logger.setLevel(logging.DEBUG)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s:%(levelname)s:[JAILED]:%(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.WARN)
    root_logger.addHandler(stream_handler)

    handler = logging.FileHandler(os.path.join(OTHELLO_STUDENT_PATH, sys.argv[-1], time.strftime("log-%Y-%m-%d-%H-%M-%S.log")))
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    log.addHandler(handler)
    root_logger.addHandler(handler)

    JailedRunner(sys.argv[-1]).run()
