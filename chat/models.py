from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class UserChatProfile(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, null=False, related_name="chat_profile")
    rooms = models.BinaryField(null=True)
    rooms_timestamp = models.BinaryField(null=True)
    last_seen = models.CharField(max_length=100, null=True)

class ChatRoomProfile(models.Model):
    room_id = models.CharField(max_length=100, null=True, unique=True)
    messages = models.BinaryField(null=True)
