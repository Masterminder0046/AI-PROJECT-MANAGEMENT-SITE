import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ProjectConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            return await self.close(code=4401)
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.group = f"project.{self.project_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(self.group, {
            "type": "presence", "user_id": self.scope["user"].id, "online": True,
        })

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_send(self.group, {
                "type": "presence", "user_id": self.scope["user"].id, "online": False,
            })
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Client -> server: typing indicators, cursor, etc.
        action = content.get("action")
        if action == "typing":
            await self.channel_layer.group_send(self.group, {
                "type": "typing", "user_id": self.scope["user"].id,
                "task_id": content.get("task_id"),
            })

    # group handlers
    async def project_event(self, event):
        await self.send_json({"event": event["event"], "data": event["data"]})

    async def presence(self, event):
        await self.send_json({"event": "presence", "data": {
            "user_id": event["user_id"], "online": event["online"]}})

    async def typing(self, event):
        await self.send_json({"event": "typing", "data": {
            "user_id": event["user_id"], "task_id": event.get("task_id")}})
