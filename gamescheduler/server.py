import asyncio
import logging
from .settings import LOGGING_HANDLERS, LOGGING_FORMATTER, LOGGING_LEVEL

log = logging.getLogger(__name__)
for handler in LOGGING_HANDLERS:
    log.addHandler(handler)
log.setLevel(LOGGING_LEVEL)

class GameScheduler(asyncio.Protocol):
    """
    Now hold on a hot minute isn't this just a Consumer but asyncio???
    Thing is, you can pass *the same* protocol object to asyncio's
    create_connection, which allows it to store a bunch of state
    unlike in Django Channels, where a new Consumer is created for
    every client.

    THE ONLY REASON I HAVE TO FORWARD REQUESTS TO THIS SERVER THROUGH
    CHANNELS IS THAT ASYNCIO DOESN'T SUPPORT WEBSOCKETS GOSH DARN IT.
    """
    def __init__(self):
        super().__init__()
        log.info("Made GameScheduler")

    def connection_made(self, transport):
        log.info("Recieved connection")

    def connection_lost(self, exc):
        log.info("Lost connection")

    def data_received(self, data):
        log.info("Recieved data {}".format(data))

    def eof_received(self):
        log.info("Recieved EOF")
