from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendrier_vaccinal, name='calendrier_vaccinal'),
    path('nutrition/', views.conseils_nutritionnels, name='conseils_nutritionnels'),
]
