# I wrote this file with no documentation by accident
# welp guess no one will ever know how it works then

import asyncio
import logging

log = logging.getLogger(__name__)

class GameSchedulerClient(asyncio.Protocol):
    def __init__(self, loop, first_callback, reg_callback):
        super().__init__()
        self.loop = loop
        self.first_callback = first_callback
        self.reg_callback = reg_callback
        self.has_recieved = False
        log.debug("Made GameSchedulerClient")

    def connection_made(self, transport):
        log.debug("Made connection")
        self.transport = transport

    def data_received(self, data):
        """
        Use two different callbacks to support the room handling code elsewhere.
        self.first_callback is usually the room setting callback, and the other
        one is the general data handling callback
        """
        log.debug("Recieved data {}".format(data))
        decoded_data = data.decode('utf-8').strip()
        
        # Handle case where multiple message were bundled together
        # Ordering is still guaranteed
        for sub_data in decoded_data.split("\n"):
            self._handle_received(sub_data)

    def _handle_received(self, decoded_data):
        if self.has_recieved:
            """
            Check if the callback is a couroutine or regular callable,
            and handle accordingly.

            lots of asyncio magic here, be careful
            """
            if asyncio.iscoroutinefunction(self.reg_callback):
                self.loop.create_task(self.reg_callback(decoded_data))
            else:
                self.loop.call_soon_threadsafe(self.reg_callback, decoded_data)
        else:
            if asyncio.iscoroutinefunction(self.first_callback):
                self.loop.create_task(self.first_callback(decoded_data))
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
