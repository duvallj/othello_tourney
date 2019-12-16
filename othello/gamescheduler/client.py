# I wrote this file with no documentation by accident
# welp guess no one will ever know how it works then

import asyncio
import logging

log = logging.getLogger(__name__)

class GameSchedulerClient(asyncio.Protocol):
    def __init__(self, loop, first_callback, reg_callback, disconnect_callback):
        super().__init__()
        self.loop = loop
        self.first_callback = first_callback
        self.reg_callback = reg_callback
        self.disconnect_callback = disconnect_callback
        self.has_received = False
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
        log.debug("Received data {}".format(data))
        decoded_data = data.decode('utf-8').strip()
        
        # Handle case where multiple message were bundled together
        # Ordering is still guaranteed
        for sub_data in decoded_data.split("\n"):
            self._handle_received(sub_data)

    def _call_asyncio_with_magic(self, func, *args):
        """
        Check if the callback is a couroutine or regular callable,
        and handle accordingly.

        lots of asyncio magic here, be careful
        """
        if asyncio.iscoroutinefunction(func):
            self.loop.create_task(func(*args))
        else:
            self.loop.call_soon_threadsafe(func, *args) 


    def _handle_received(self, decoded_data):
        if self.has_received:
            self._call_asyncio_with_magic(self.reg_callback, decoded_data)
        else:
            self._call_asyncio_with_magic(self.first_callback, decoded_data)
            self.has_received = True

    def connection_lost(self, exc):
        log.debug("Lost connection")
        self._call_asyncio_with_magic(self.disconnect_callback, exc)


    def eof_received(self):
        log.debug("Received EOF")


def game_scheduler_client_factory(loop, first_callback, reg_callback, disconnect_callback):
    def _internal_factory():
        return GameSchedulerClient(loop, first_callback, reg_callback, disconnect_callback)
    return _internal_factory
