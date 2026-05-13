from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from apps.notifications.models import Notification


def push_notification(user, *, kind, title, body="", url="", actor=None):
    n = Notification.objects.create(
        recipient=user, actor=actor, kind=kind, title=title, body=body, url=url
    )
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(f"user.{user.id}", {
        "type": "notify",
        "data": {"id": n.id, "kind": kind, "title": title, "body": body, "url": url,
                 "is_read": False, "created_at": n.created_at.isoformat()},
    })
    return n
