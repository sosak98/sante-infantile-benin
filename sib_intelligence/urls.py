from django.urls import path
from . import views

app_name = 'sib'

urlpatterns = [
    path('', views.triage, name='triage'),
    path('chat/', views.chat, name='sib_chat'),
]
