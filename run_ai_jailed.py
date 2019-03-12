import os, sys
import logging as log

from othello.gamescheduler.run_ai_utils import JailedRunner

if __name__=="__main__":
    log.basicConfig(format='%(asctime)s:%(levelname)s:[JAILED]:%(message)s', level=log.WARN)
    JailedRunner(sys.argv[-1]).run()
