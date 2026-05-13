import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_asgi_application()

from websocket.routing import websocket_urlpatterns  # noqa: E402
from websocket.middleware import JWTAuthMiddlewareStack  # noqa: E402

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
