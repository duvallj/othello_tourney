from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from django.conf.urls import url
from .apps.games.consumers import GamePlayingConsumer, GameWatchingConsumer

print("Routing application imported??")

application = ProtocolTypeRouter({
    'websocket':  URLRouter([
        url(
            r"^ws/play/(?=.*black=(?P<black>[\w\d-]+))(?=.*white=(?P<white>[\w\d-]+))(?=.*t=(?P<t>[\d\.]+))",
            GamePlayingConsumer
        ),
        url(
            r"^ws/watch/(?=.*watching=(?P<watching>[\w\d]+))",
            GameWatchingConsumer
        ),
    ]),
    'channel': ChannelNameRouter({
        # empty
    })
})
