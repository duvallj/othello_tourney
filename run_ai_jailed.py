import os, sys
import logging as log

from othello.apps.games.worker import JailedRunner

if __name__=="__main__":
    log.basicConfig(format='%(asctime)s:%(levelname)s:[JAILED]:%(message)s', level=log.DEBUG)
    """
    student_folder = os.path.join(os.getcwd(), 'students')
    folders = os.listdir(student_folder)
    log.debug('Listed student folders successfully')
    possible_names =  {x for x in folders if \
        x != '__pycache__' and \
        os.path.isdir(os.path.join(student_folder, x))
    }
    """
    JailedRunner.run()
