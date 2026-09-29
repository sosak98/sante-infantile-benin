from django.urls import path
from . import views

app_name = 'sante'

urlpatterns = [
    path('', views.carte, name='carte'),
    path('vaccination/', views.jours_vaccination, name='jours_vaccination'),
    path('osm/', views.etablissements_osm, name='etablissements_osm'),
]
