from django.urls import re_path
from websocket.consumers.project import ProjectConsumer
from websocket.consumers.notifications import NotificationsConsumer

websocket_urlpatterns = [
    re_path(r"ws/projects/(?P<project_id>\d+)/$", ProjectConsumer.as_asgi()),
    re_path(r"ws/notifications/$", NotificationsConsumer.as_asgi()),
]
