from django.urls import path

from apps.ai import views

app_name = "ai"

urlpatterns = [
    path("chat/", views.chat_page, name="chat"),
    path("chat/stream/", views.chat_stream, name="chat_stream"),
    path("chat/feedback/", views.chat_feedback, name="chat_feedback"),
    path("foto/", views.photo_upload, name="photo_upload"),
    path("foto/<uuid:search_id>/", views.photo_status, name="photo_status"),
]
