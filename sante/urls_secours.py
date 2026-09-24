"""URL racine du module « Premiers secours & signes de danger » (sans namespace)."""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.premiers_secours, name='premiers_secours'),
]
