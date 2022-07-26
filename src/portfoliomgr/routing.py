from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from alerts.consumers import NoseyConsumer
from channels.auth import AuthMiddlewareStack
import alerts.routing
from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(URLRouter(
            alerts.routing.websocket_urlpatterns
        )),
    "http": get_asgi_application()
})
