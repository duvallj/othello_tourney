import asyncio
import os
import logging

from othello.gamescheduler.tournament_server import RRTournamentScheduler, BracketTournamentScheduler
from othello.gamescheduler.tournament_utils import ResultsCSVWriter
from othello.gamescheduler.utils import get_possible_strats
from othello.gamescheduler.settings import SCHEDULER_HOST, SCHEDULER_PORT, PROJECT_ROOT

LOGGING_FORMATTER = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s %(message)s')
LOGGING_LEVEL = logging.DEBUG
LOGGING_HANDLERS = [
    logging.StreamHandler(),
    logging.FileHandler('gs.log',mode='w'),
]
for handler in LOGGING_HANDLERS:
    handler.setFormatter(LOGGING_FORMATTER)

log = logging.getLogger('othello.gamescheduler')
for handler in LOGGING_HANDLERS:
    log.addHandler(handler)
log.setLevel(LOGGING_LEVEL)

TOURNAMENT_NUM = 4
TOURNAMENT_TIMELIMIT = 5
TOURNAMENT_GAMES = 10
AI_LIST = ["2021dhan", "2020scriado", "2020rmuruges", "2020dsun", "2020jdapaah", "2020akumar", "2020bpark", "2020jgong", "2020kilanche", "2020pwadhwa", "2020agupta", "2019gharriso", "2020pgunnam", "2020mhuang", "2020skatin", "2020vsharma", "2020rmittal", "2020aliang", "2020siyer", "2020bhu", "2020rhamilto", "2020dchen", "2020dli"]#list(get_possible_strats())
TOURNAMENT_FILE = os.path.join(PROJECT_ROOT, 'tournament-{}'.format(TOURNAMENT_NUM))


def write_results(results, results_lock):
    log.info("Writing results!")

    writer = ResultsCSVWriter(TOURNAMENT_FILE)
    with results_lock:
        writer.write(results)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    gs = RRTournamentScheduler(loop, completed_callback=write_results, ai_list=AI_LIST, timelimit=TOURNAMENT_TIMELIMIT, max_games=TOURNAMENT_GAMES)
    def game_scheduler_factory(): return gs
    coro = loop.create_server(game_scheduler_factory, host=SCHEDULER_HOST, port=SCHEDULER_PORT)
    server = loop.run_until_complete(coro)

    # Server requests until Ctrl+C is pressed
    log.info("Running server")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    log.info("Stopping server")
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
