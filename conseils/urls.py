from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendrier_vaccinal, name='calendrier_vaccinal'),
    path('rdv/', views.calculer_rdv, name='calculer_rdv'),
    path('nutrition/', views.conseils_nutritionnels, name='conseils_nutritionnels'),
]
