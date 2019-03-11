import asyncio
import logging

from .settings import LOGGING_HANDLERS, LOGGING_FORMATTER, LOGGING_LEVEL

log = logging.getLogger(__name__)
for handler in LOGGING_HANDLERS:
    log.addHandler(handler)
log.setLevel(LOGGING_LEVEL)

class GameSchedulerClient(asyncio.Protocol):
    def __init__(self, loop, first_callback, reg_callback):
        super().__init__()
        self.loop = loop
        self.first_callback = first_callback
        self.reg_callback = reg_callback
        self.has_recieved = False
        log.debug("Made GameSchedulerClient")

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        log.debug("Recieved data {}".format(data))
        decoded_data = data.decode('utf-8').strip()
        if self.has_recieved:
            self.loop.call_soon_threadsafe(self.reg_callback, decoded_data)
        else:
            self.loop.call_soon_threadsafe(self.first_callback, decoded_data)
            self.has_recieved = True

    def connection_lost(self, exc):
        log.debug("Lost connection")

    def eof_received(self):
        log.debug("Recieved EOF")


def game_scheduler_client_factory(loop, first_callback, reg_callback):
    def _internal_factory():
        return GameSchedulerClient(loop, first_callback, reg_callback)
    return _internal_factory
