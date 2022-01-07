from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["picture"]


class RegisterUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password", "profile", "id"]
        extra_kwargs = {'password': {'write_only': True}, 'id': {'read_only': True}}
