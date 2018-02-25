from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from django.conf.urls import url
from .apps.games.consumers import GameServingConsumer

application = ProtocolTypeRouter({
    'websocket':  URLRouter([
        url(r"^ws/", GameServingConsumer),
    ]),
    'channel': ChannelNameRouter({
        # empty
    })
})