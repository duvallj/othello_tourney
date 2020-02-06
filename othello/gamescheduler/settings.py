import os, sys
import datetime
import logging

# Main settings file for the GameScheduler
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

OTHELLO_STUDENT_PATH = os.path.join(PROJECT_ROOT, 'students')
OTHELLO_PUBLIC_PATH = os.path.join(PROJECT_ROOT, 'othello', 'public')

OTHELLO_AI_HUMAN_PLAYER = "Yourself"
OTHELLO_AI_UNKNOWN_PLAYER = "Unknown"
OTHELLO_AI_NAME_REPLACE = "=NAME="
# DEVEL: set this to "python -u {2} {3}".format(...)
#OTHELLO_AI_RUN_COMMAND = "python -u {2} {3}".format(
OTHELLO_AI_RUN_COMMAND = "firejail --quiet --profile={0} --whitelist={1} --read-only={1}/strategy.py python3 -u {2} {3}".format(
#OTHELLO_AI_RUN_COMMAND = "cpulimit -l 25 -- firejail --quiet --profile={0} --whitelist={1} --read-only={1}/strategy.py python3 -u {2} {3}".format(
    os.path.join(PROJECT_ROOT, "python-custom.profile"),
    os.path.join(OTHELLO_STUDENT_PATH, OTHELLO_AI_NAME_REPLACE),
    os.path.join(PROJECT_ROOT, "run_ai_jailed.py"),
    OTHELLO_AI_NAME_REPLACE,
)

OTHELLO_AI_MAX_TIME = 60
OTHELLO_GAME_MAX_TIME = OTHELLO_AI_MAX_TIME * 75 # fairly arbitrary, don't want to limit people's games too much
OTHELLO_GAME_MAX_TIMEDELTA = datetime.timedelta(seconds=OTHELLO_GAME_MAX_TIME)

SCHEDULER_HOST = "127.0.0.1"
SCHEDULER_PORT = 13770
