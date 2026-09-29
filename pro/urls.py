from django.urls import path

from . import views

app_name = 'pro'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('inscription/', views.inscription, name='inscription'),
    path('en-attente/', views.en_attente, name='en_attente'),
    path('tableau-de-bord/', views.tableau_de_bord, name='tableau_de_bord'),
    path('mon-centre/', views.fiche_centre, name='fiche_centre'),
    path('outil-pev/', views.outil_pev, name='outil_pev'),
]
