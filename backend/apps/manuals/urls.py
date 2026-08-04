from django.urls import path

from apps.manuals import views

app_name = "manuals"

urlpatterns = [
    path("revisao/", views.review_queue, name="review_queue"),
    path("revisao/<int:pk>/", views.review_detail, name="review_detail"),
]
