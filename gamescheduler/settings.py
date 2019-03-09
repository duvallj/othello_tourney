import os, sys
import logging

# Main settings file for the GameScheduler
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

OTHELLO_STUDENT_PATH = os.path.join(PROJECT_ROOT, 'students')
OTHELLO_PUBLIC_PATH = os.path.join(OTHELLO_STUDENT_PATH, 'public')

OTHELLO_AI_HUMAN_PLAYER = "Yourself"
OTHELLO_AI_NAME_REPLACE = "=NAME="
# DEVEL: set this to "python -u {2} =NAME=".format(...)
OTHELLO_AI_RUN_COMMAND = "firejail --quiet --profile={0} --whitelist={1} python3 -u {2} {3}".format(
    os.path.join(PROJECT_ROOT, "python-custom.profile"),
    os.path.join(OTHELLO_STUDENT_PATH, OTHELLO_AI_NAME_REPLACE),
    os.path.join(PROJECT_ROOT, "run_ai_jailed.py"),
    OTHELLO_AI_NAME_REPLACE,
)

SCHEDULER_HOST = "127.0.0.1"
SCHEDULER_PORT = 13770

LOGGING_FORMATTER = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s %(message)s')
LOGGING_LEVEL = logging.DEBUG
LOGGING_HANDLERS = [
    logging.StreamHandler(),
]
for handler in LOGGING_HANDLERS:
    handler.setFormatter(LOGGING_FORMATTER)
