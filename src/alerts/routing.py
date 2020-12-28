from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/alerts/', consumers.NoseyConsumer.as_asgi()),
]