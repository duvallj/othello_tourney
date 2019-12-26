import asyncio
import os
import logging

from othello.gamescheduler.tournament_server import RRTournamentScheduler, BracketTournamentScheduler
from othello.gamescheduler.tournament_utils import ResultsCSVWriter
from othello.gamescheduler.utils import get_possible_strats
from othello.gamescheduler.settings import SCHEDULER_HOST, SCHEDULER_PORT, PROJECT_ROOT

LOGGING_FORMATTER = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s %(message)s')
LOGGING_LEVEL = logging.INFO
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
AI_LIST = list(get_possible_strats())
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
