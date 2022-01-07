from django.db import models
from django.contrib.auth.models import User
import os
from django.conf import settings


# Create your models here.

def upload_format_profile_pic(instance, filename):
    initials = 'profile_pictures'
    ext = os.path.splitext(filename)[-1]
    new_name = instance.owner.username.lower().replace(' ', "_") + ext
    path = os.path.join(settings.MEDIA_ROOT, initials, new_name)
    if os.path.exists(path):
        os.remove(path)
    return os.path.join(initials, new_name)


class Profile(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, null=False, related_name="profile")
    picture = models.ImageField(upload_to=upload_format_profile_pic, null=False, blank=False)
    date_last_modified = models.DateTimeField(auto_now=True)

