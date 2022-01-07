from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from .views import RegisterUser, LogoutUser

urlpatterns = [
    path('login', TokenObtainPairView.as_view(), name="auth_token_obtain_pair"),
    path('refresh_token', TokenRefreshView.as_view(), name="auth_token_refresh"),
    path('logout', LogoutUser.as_view(), name="auth_logout"),
    path('register', RegisterUser.as_view(), name="auth_register"),
]
