from django.urls import path
from . import views

urlpatterns = [
    path('', views.carte, name='carte'),
]
