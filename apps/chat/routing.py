from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/chat/(?P<uuid_conversa>[0-9a-f-]+)/$", consumers.ConsumidorChat.as_asgi()
    ),
]
