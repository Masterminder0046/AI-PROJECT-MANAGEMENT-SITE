from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_task_event(project_id: int, event: str, payload: dict):
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(f"project.{project_id}", {
        "type": "project.event", "event": event, "data": payload,
    })
