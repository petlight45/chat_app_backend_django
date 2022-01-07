from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserChatProfile, ChatRoomProfile
from auth_.serializers import ProfileSerializer, RegisterUserSerializer
import orjson


class UserChatProfileSerializer(serializers.ModelSerializer):
    owner = RegisterUserSerializer(read_only=True)
    room_config = serializers.SerializerMethodField(read_only=True)
    room_config_timestamps = serializers.SerializerMethodField(read_only=True)

    def get_room_config(self, instance):
        return orjson.loads(instance.rooms) if instance.rooms else {}

    def get_room_config_timestamps(self, instance):
        return orjson.loads(instance.rooms_timestamp) if instance.rooms_timestamp else {}

    class Meta:
        model = UserChatProfile
        fields = ["owner", "room_config", "room_config_timestamps", "last_seen"]


class ChatRoomProfileSerializerMessages(serializers.ModelSerializer):
    room_messages = serializers.SerializerMethodField(read_only=True)

    def get_room_messages(self, instance):
        return orjson.loads(instance.messages) if instance.messages else {}

    class Meta:
        model = ChatRoomProfile
        fields = ["room_id", "room_messages"]

