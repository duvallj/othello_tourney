from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from django.conf.urls import url
from .apps.games.consumers import GamePlayingConsumer, GameWatchingConsumer

print("Routing application imported??")

application = ProtocolTypeRouter({
    'websocket':  URLRouter([
        url(r"^ws/play", GamePlayingConsumer),
        url(r"^ws/watch", GameWatchingConsumer),
    ]),
    'channel': ChannelNameRouter({
        # empty
    })
})
