import json

import orjson
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, JsonWebsocketConsumer
import secrets

from django.contrib.auth.models import User
from django.utils import timezone
from .models import ChatRoomProfile, UserChatProfile
from copy import deepcopy


def generate_message_id():
    return secrets.token_hex(40) + str(timezone.now().timestamp())


def get_room_object(roomID):
    if ChatRoomProfile.objects.filter(room_id=roomID).exists():
        return ChatRoomProfile.objects.get(room_id=roomID)
    return ChatRoomProfile.objects.create(room_id=roomID, messages=orjson.dumps({}))


def save_received_message(roomID, message, sender, receiver):
    sender = str(sender) if type(sender) != str else sender
    receiver = str(receiver) if type(receiver) != str else receiver
    message_id = generate_message_id()
    room_obj = get_room_object(roomID)
    to_save_data = {
        "message": message,
        "sender": sender,
        "receiver": receiver,
        "isRead": "0",
        "timestamp": str(timezone.now().isoformat())
    }
    room_obj_messages = orjson.loads(room_obj.messages)
    room_obj_messages[message_id] = to_save_data
    room_obj.messages = orjson.dumps(room_obj_messages)
    room_obj.save()


def get_chat_profile(user_obj):
    user_chat_profile = getattr(user_obj, 'chat_profile', None)
    if not user_chat_profile:
        instance = UserChatProfile.objects.create(owner=user_obj, rooms=orjson.dumps({}))
        return instance
    return user_chat_profile


def update_latest_room_on_sending_message(sender_id, receiver_id):
    sender_id = int(sender_id) if type(sender_id) == str else sender_id
    receiver_id = int(receiver_id) if type(receiver_id) == str else receiver_id
    sender = User.objects.get(id=sender_id)
    receiver = User.objects.get(id=receiver_id)
    # Sender
    room_config = get_chat_profile(sender)
    room_config_timestamps_loaded = orjson.loads(room_config.rooms_timestamp) if room_config.rooms_timestamp else {}
    room_config_timestamps_loaded[str(receiver_id)] = str(timezone.now().timestamp())
    room_config.rooms_timestamp = orjson.dumps(room_config_timestamps_loaded)
    room_config.save()

    ##For Guest User
    room_config = get_chat_profile(receiver)
    room_config_timestamps_loaded = orjson.loads(room_config.rooms_timestamp) if room_config.rooms_timestamp else {}
    room_config_timestamps_loaded[str(sender_id)] = str(timezone.now().timestamp())
    room_config.rooms_timestamp = orjson.dumps(room_config_timestamps_loaded)
    room_config.save()


def update_last_seen(user):
    chat_profile = user.chat_profile
    chat_profile.last_seen = timezone.now().isoformat()
    chat_profile.save()


online_users = set()


class ChatConsumer(WebsocketConsumer):
    global_group_name = "global_group"

    def connect(self):
        self.one_to_one_group = None
        self.room_refreshed = False
        async_to_sync(self.channel_layer.group_add)(
            self.global_group_name,
            self.channel_name
        )
        online_users.add(self.scope.get('user').id)
        async_to_sync(self.channel_layer.group_send)(
            self.global_group_name,
            {
                'type': 'online_users',
                "data": json.dumps(list(online_users))
            }
        )
        self.accept()

    def disconnect(self, close_code):
        update_last_seen(self.scope.get("user"))
        try:
            online_users.remove(self.scope.get('user').id)
            async_to_sync(self.channel_layer.group_send)(
                self.global_group_name,
                {
                    'type': 'online_users',
                    "data": json.dumps(list(online_users))
                }
            )
        except KeyError:
            pass
        async_to_sync(self.channel_layer.group_discard)(
            self.global_group_name,
            self.channel_name
        )
        if self.one_to_one_group:
            async_to_sync(self.channel_layer.group_discard)(
                self.one_to_one_group,
                self.channel_name
            )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type = text_data_json.get("type")
        data = text_data_json.get("data")
        if type == "room_message":
            room_id = data.get("room_id")
            if room_id != self.one_to_one_group:
                self.send(text_data=json.dumps({
                    "type": "room_message_fail",
                    "data": {
                        'message': "You've not yet joined this room",
                        'room_id': room_id
                    }
                }))
                return
            sender = self.scope.get('user').id
            receiver = data.get("receiver")
            pending_list_id = data.get('pending_list_id')
            print(self.room_refreshed)
            if not self.room_refreshed:
                update_latest_room_on_sending_message(sender, receiver)
                async_to_sync(self.channel_layer.group_send)(
                    self.one_to_one_group,
                    {
                        'type': 'sent_first_room_message',
                        "data": json.dumps({
                            'room_id': room_id
                        })
                    }
                )
                self.room_refreshed = True
            message = data.get("message")
            try:
                save_received_message(room_id, message, sender, receiver)
                async_to_sync(self.channel_layer.group_send)(
                    self.one_to_one_group,
                    {
                        'type': 'chat_message',
                        "data": json.dumps({
                            'room_id': room_id,
                            'sender': sender,
                            'receiver': receiver,
                            "pending_list_id": pending_list_id
                        })
                    }
                )
                async_to_sync(self.channel_layer.group_send)(
                    self.global_group_name,
                    {
                        'type': 'new_message_broadcast',
                        "data": json.dumps({
                            'room_id': room_id
                        })
                    }
                )
            except Exception as err:
                self.send(text_data=json.dumps({
                    "type": "room_message_failed",
                    "data": {
                        'message': str(err),
                        'room_id': room_id,
                        'sender': sender,
                        'receiver': receiver
                    }
                }))
        elif type == "join_group":
            room_id = data.get("room_id")
            if self.one_to_one_group:
                async_to_sync(self.channel_layer.group_discard)(
                    self.one_to_one_group,
                    self.channel_name
                )
            self.room_refreshed = False
            self.one_to_one_group = room_id
            async_to_sync(self.channel_layer.group_add)(
                room_id,
                self.channel_name
            )
            self.send(text_data=json.dumps({
                "type": "join_group_success",
                "data": {
                    "room_id": room_id
                }
            }))
        elif type == "room_messages_read":
            room_id = data.get("room_id")
            sender = str(self.scope.get('user').id)
            async_to_sync(self.channel_layer.group_send)(
                room_id,
                {
                    "type": "room_messages_read_success",
                    "data": json.dumps({
                        "room_id": room_id,
                        "sender": sender
                    })
                }
            )

    # Receive message from room group
    def chat_message(self, event):
        data = event['data']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            "type": "room_message_success",
            "data": json.loads(data)
        }))

    def online_users(self, event):
        data = event['data']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            "type": "online_users_notification",
            "data": json.loads(data)
        }))

    def sent_first_room_message(self, event):
        data = event['data']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            "type": "sent_first_room_message",
            "data": json.loads(data)
        }))

    def new_message_broadcast(self, event):
        data = event['data']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            "type": "new_message_broadcast",
            "data": json.loads(data)
        }))

    def room_messages_read_success(self, event):
        data = event['data']
        self.send(text_data=json.dumps({
            "type": "room_messages_read_success",
            "data": json.loads(data)
        }))
