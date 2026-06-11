from django.urls import path
from . import views

urlpatterns = [
    path('', views.triage, name='triage'),
    path('chat/', views.chat, name='sib_chat'),
]
