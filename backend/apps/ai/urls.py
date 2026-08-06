from django.urls import path

from apps.ai import views

app_name = "ai"

urlpatterns = [
    path("chat/", views.chat_page, name="chat"),
    path("chat/stream/", views.chat_stream, name="chat_stream"),
    path("chat/feedback/", views.chat_feedback, name="chat_feedback"),
]
