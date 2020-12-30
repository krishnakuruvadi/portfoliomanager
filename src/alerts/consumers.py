from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Alert

class NoseyConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("gossip", self.channel_name)
        print(f"Added {self.channel_name} channel to gossip")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("gossip", self.channel_name)
        print(f"Removed {self.channel_name} channel to gossip")

    async def receive(self, text_data):
        print(text_data)
        if text_data == "giveAlertCount":
            await self.send(text_data=json.dumps({
                "type": "alert.gossip",
                "event": "Alert Count",
                "count": len(Alert.objects.filter(seen=False))
            }))
        else:
            text_data_json = json.loads(text_data)
            event = text_data_json['event']
            count = text_data_json['count']

            await self.channel_layer.group_send(
                "gossip",
                json.dumps({
                    'type': 'alert_gossip',
                    'event': event,
                    'count': count,
                }).encode("utf-8")
            )

    async def alert_gossip(self, event):
        eve = event['event']
        count = event['count']
        print(f"Got message {event} at {self.channel_name}")
        await self.send(text_data=json.dumps({
            'event': eve,
            'count': count,
        }).encode("utf-8"))
    pass