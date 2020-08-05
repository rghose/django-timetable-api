from django.urls import path

from . import views

urlpatterns = [
    path('', views.handle_ping),
    path('interview', views.handle_interview_request)
]
