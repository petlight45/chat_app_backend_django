from django.urls import path
from .views import FetchUserChatProfile, FetchAllUsersView, CreateRoomView, FetchAllMessagesInChatRoomView, \
    ReadAllMessagesInChatRoomView, FetchUnreadMessagesInChatRoomCountView, FetchUserLastSeen

urlpatterns = [
    path('api/chat/user/profile', FetchUserChatProfile.as_view(), name="chat_user_profile"),
    path('api/chat/user/all', FetchAllUsersView.as_view(), name="chat_user_all"),
    path('api/chat/user/room/create', CreateRoomView.as_view(), name="chat_user_room_create"),
    path('api/chat/user/get/last_seen/<int:user_id>/', FetchUserLastSeen.as_view(), name="chat_user_get_last_seen"),
    path('api/chat/room/messages/<str:room_id>/', FetchAllMessagesInChatRoomView.as_view(), name="chat_room_messages"),
    path('api/chat/room/messages/read/all/<str:room_id>/', ReadAllMessagesInChatRoomView.as_view(),
         name="chat_room_messages_read_all"),
    path('api/chat/room/messages/unread_count/<str:room_id>/', FetchUnreadMessagesInChatRoomCountView.as_view(),
         name="chat_room_messages_read_all")
]
