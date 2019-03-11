import asyncio
from django.conf import settings
import json

from ...gamescheduler.client import game_scheduler_client_factory

class GameListRetriever:
    def __init__(self, loop):
        self.loop = loop
        # Python 3.6 holdback, 3.7 code should use
        #self.fut = self.loop.get_future()
        self.fut = asyncio.Future(loop=loop)
        self.room_id = None

    def recieve(self, data):
        self.fut.set_result(json.loads(data))
        self.transport.close()

    def first_init(self, data):
        self.room_id = data

        content = {
            'type': 'list_request',
            'room_id': self.room_id,
        }
        encoded_content = json.dumps(content).encode('utf-8')
        self.transport.write(encoded_content)

    async def get(self):
        self.transport, self.protocol = await self.loop.create_connection(
            game_scheduler_client_factory(self.loop, self.first_init, self.recieve),
            host=settings.SCHEDULER_HOST,
            port=settings.SCHEDULER_PORT
        )


# ha     haha      HAhaha   HAHAHA HAHAHAHAHAHAHA
# what have i done
async def get_playing_rooms():
    loop = asyncio.get_event_loop()
    glr = GameListRetriever(loop)
    await glr.get()
    await glr.fut
    return glr.fut.result()
