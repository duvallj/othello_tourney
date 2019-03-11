import asyncio
import logging

from othello.gamescheduler.server import GameScheduler
from othello.gamescheduler.settings import SCHEDULER_HOST, SCHEDULER_PORT
from othello.gamescheduler.settings import LOGGING_HANDLERS, LOGGING_FORMATTER, LOGGING_LEVEL

log = logging.getLogger(__name__)
for handler in LOGGING_HANDLERS:
    log.addHandler(handler)
log.setLevel(LOGGING_LEVEL)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    gs = GameScheduler(loop)
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
