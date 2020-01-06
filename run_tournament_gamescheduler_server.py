import asyncio
import os
import logging
import django

# Needed to get Django ORM to work
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "othello.settings")
django.setup()

from othello.gamescheduler.tournament_server import SetTournamentScheduler, SwissTournamentScheduler
from othello.apps.tournament.utils import reset_or_create_tournament, create_round_robin, create_everyone_vs, create_single_elim_bracket, ResultsCSVWriter
from othello.gamescheduler.utils import get_possible_strats
from othello.gamescheduler.settings import SCHEDULER_HOST, SCHEDULER_PORT, PROJECT_ROOT

from analyze_tournament_csv import read_rankings

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

TOURNAMENT_NUM = 6
TOURNAMENT_TIMELIMIT = 5
TOURNAMENT_GAMES = 12
AI_LIST = read_rankings("round{}-rankings.txt".format(TOURNAMENT_NUM-1))[:16]
TOURNAMENT_NAME = os.path.join(PROJECT_ROOT, 'tournament-{}'.format(TOURNAMENT_NUM))

def write_results(results, results_lock):
    log.info("Writing results!")

    writer = ResultsCSVWriter(TOURNAMENT_NAME)
    with results_lock:
        writer.write(results)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    tournament = reset_or_create_tournament(TOURNAMENT_NAME)
    #SET_LIST = create_round_robin(AI_LIST, tournament)
    #SET_LIST = create_everyone_vs(AI_LIST, tournament, who="random")
    SET_LIST = create_single_elim_bracket(AI_LIST, tournament)
    
    gs = SetTournamentScheduler(tournament, loop, completed_callback=write_results, ai_list=AI_LIST, sets=SET_LIST, timelimit=TOURNAMENT_TIMELIMIT, max_games=TOURNAMENT_GAMES)
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
    write_results(gs.sets, gs.results_lock)
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
