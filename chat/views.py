from django.contrib.auth.models import User
from django.shortcuts import render
# Create your views here.
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import UserChatProfile, ChatRoomProfile
import orjson
from .serializers import UserChatProfileSerializer, ChatRoomProfileSerializerMessages
from auth_.serializers import RegisterUserSerializer
import secrets
from django.utils import timezone
from rest_framework import status
from copy import deepcopy


class FetchUserChatProfile(RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    serializer_class = UserChatProfileSerializer

    def get_object(self):
        auth_user_chat_profile = getattr(self.request.user, 'chat_profile', None)
        if (not auth_user_chat_profile):
            instance = UserChatProfile.objects.create(owner=self.request.user, rooms=orjson.dumps({}))
            return instance
        return auth_user_chat_profile


class FetchAllUsersView(ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    serializer_class = RegisterUserSerializer

    def get_queryset(self):
        return User.objects.exclude(id=self.request.user.id).all()


class CreateRoomView(CreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def generate_room_name(self):
        return secrets.token_hex(40) + str(timezone.now().timestamp())

    def get_chat_profile(self, user_obj):
        user_chat_profile = getattr(user_obj, 'chat_profile', None)
        if (not user_chat_profile):
            instance = UserChatProfile.objects.create(owner=user_obj, rooms=orjson.dumps({}))
            return instance
        return user_chat_profile

    def post(self, request, *args, **kwargs):
        other_user_id = request.data.get("user_id")
        room_name = self.generate_room_name()

        ###For Auth User
        old_room_config = self.get_chat_profile(self.request.user)
        old_room_config_loaded = orjson.loads(old_room_config.rooms) if old_room_config.rooms else {}
        old_room_config_loaded[str(other_user_id)] = room_name
        old_room_config.rooms = orjson.dumps(old_room_config_loaded)

        old_room_config_timestamps_loaded = orjson.loads(
            old_room_config.rooms_timestamp) if old_room_config.rooms_timestamp else {}
        old_room_config_timestamps_loaded[str(other_user_id)] = str(timezone.now().timestamp())
        old_room_config.rooms_timestamp = orjson.dumps(old_room_config_timestamps_loaded)
        old_room_config.save()

        ##For Guest User
        old_room_config = self.get_chat_profile(User.objects.get(id=other_user_id))
        old_room_config_loaded = orjson.loads(old_room_config.rooms) if old_room_config.rooms else {}
        old_room_config_loaded[str(self.request.user.id)] = room_name
        old_room_config.rooms = orjson.dumps(old_room_config_loaded)

        old_room_config_timestamps_loaded = orjson.loads(
            old_room_config.rooms_timestamp) if old_room_config.rooms_timestamp else {}
        old_room_config_timestamps_loaded[str(self.request.user.id)] = str(timezone.now().timestamp())
        old_room_config.rooms_timestamp = orjson.dumps(old_room_config_timestamps_loaded)
        old_room_config.save()

        # Creating the actual room
        ChatRoomProfile.objects.create(room_id=room_name, messages=orjson.dumps({}))
        return Response(room_name, status=status.HTTP_200_OK)


class FetchAllMessagesInChatRoomView(RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    serializer_class = ChatRoomProfileSerializerMessages

    def get_object(self):
        if ChatRoomProfile.objects.filter(room_id=self.kwargs.get("room_id")).exists():
            return ChatRoomProfile.objects.get(room_id=self.kwargs.get("room_id"))
        return None


class ReadAllMessagesInChatRoomView(UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    serializer_class = ChatRoomProfileSerializerMessages

    def get_object(self):
        if ChatRoomProfile.objects.filter(room_id=self.kwargs.get("room_id")).exists():
            return ChatRoomProfile.objects.get(room_id=self.kwargs.get("room_id"))
        return ChatRoomProfile.objects.create(room_id=self.kwargs.get("room_id"), messages=orjson.dumps({}))

    def put(self, request, *args, **kwargs):
        auth_user_id = self.request.user.id
        room_obj = self.get_object()
        room_messages_loaded = orjson.loads(room_obj.messages) if room_obj.messages else {}
        count = 0
        for message_id in room_messages_loaded.keys():
            if room_messages_loaded[message_id].get("receiver", None) == str(auth_user_id) and room_messages_loaded[
                message_id].get(
                "isRead", None) == "0":
                room_messages_loaded[message_id]["isRead"] = "1"
                room_messages_loaded[message_id]["timeRead"] = timezone.now().isoformat()
                count += 1
        if count:
            room_obj.messages = orjson.dumps(room_messages_loaded)
            room_obj.save()
        return Response({"status": "success"}, status=status.HTTP_200_OK)


class FetchUnreadMessagesInChatRoomCountView(RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get_object(self):
        if ChatRoomProfile.objects.filter(room_id=self.kwargs.get("room_id")).exists():
            return ChatRoomProfile.objects.get(room_id=self.kwargs.get("room_id"))
        return ChatRoomProfile.objects.create(room_id=self.kwargs.get("room_id"), messages=orjson.dumps({}))

    def get(self, request, *args, **kwargs):
        auth_user_id = self.request.user.id
        room_obj = self.get_object()
        room_messages_loaded = orjson.loads(room_obj.messages) if room_obj.messages else {}
        count = 0
        for message_id in room_messages_loaded.keys():
            if room_messages_loaded[message_id].get("receiver", None) == str(auth_user_id) and room_messages_loaded[
                message_id].get(
                "isRead", None) == "0":
                count += 1
        return Response({'count': count}, status=status.HTTP_200_OK)


class FetchUserLastSeen(RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get_object(self):
        user_obj = User.objects.get(id=int(self.kwargs.get("user_id")))
        auth_user_chat_profile = getattr(user_obj, 'chat_profile', None)
        if (not auth_user_chat_profile):
            instance = UserChatProfile.objects.create(owner=user_obj, rooms=orjson.dumps({}))
            return instance
        return auth_user_chat_profile

    def get(self, request, *args, **kwargs):
        room_obj = self.get_object()
        return Response({'last_seen': room_obj.last_seen}, status=status.HTTP_200_OK)
