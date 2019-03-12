from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from django.conf.urls import url
from .apps.games.consumers import GamePlayingConsumer, GameWatchingConsumer

"""
These routes have fancy regex to pass their arguments through
Basically, all the args are positive lookaheads (so they can be specified in
any order, not that it matters), with the key inside and a named capturing group
for a character subset afterwards.

If you took Gabor AI you should know what that all means.
"""

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
