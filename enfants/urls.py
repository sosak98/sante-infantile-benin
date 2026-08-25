from django.urls import path
from . import views

app_name = 'enfants'

urlpatterns = [
    path('', views.detection_malnutrition, name='detection_malnutrition'),
]
