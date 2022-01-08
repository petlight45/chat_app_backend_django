import os
import os
from pathlib import Path
from dotenv import load_dotenv
print(os.getcwd())
load_dotenv("env/.env")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_server.settings')

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import django
django.setup()
import chat.routing
from chat.middlewares import TokenAuthMiddleware

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
