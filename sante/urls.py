from django.urls import path
from . import views

urlpatterns = [
    path('', views.carte, name='carte'),
    path('osm/', views.etablissements_osm, name='etablissements_osm'),
    path('charger-seeds/', views.charger_seeds, name='charger_seeds'),
]
