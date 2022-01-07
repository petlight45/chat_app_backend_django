from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from .serializers import RegisterUserSerializer, ProfileSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.response import Response
from .models import Profile


class RegisterUser(CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        username = request.data.get('username')
        print(email, username)
        if email and User.objects.filter(email=email.strip()).exists():
            return Response({"message": f"Someone already registered an account with the email '{email}'"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
        elif username and User.objects.filter(username=username.strip()).exists():
            return Response({"message": f"Someone already registered an account with the username '{username}'"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
        else:

            user = super().post(request, *args, **kwargs)
            profile_serializer = ProfileSerializer(data=request.data)
            try:
                profile_serializer.is_valid(raise_exception=True)
                Profile.objects.create(owner=user, picture=request.data.get("picture"))
                return Response({"message": "Your account have been created, you can proceed and login!"},
                                status=status.HTTP_201_CREATED)
            except Exception as err:
                print(err.__class__)
                user.delete()
                return Response({"message": "Error in processing uploaded profile picture!"},
                                status=status.HTTP_406_NOT_ACCEPTABLE)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.perform_create(serializer)

    def perform_create(self, serializer):
        return serializer.save()


class LogoutUser(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
