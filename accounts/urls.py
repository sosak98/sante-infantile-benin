from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('a-propos/', views.about, name='a_propos'),

    # Authentification
    path('inscription/', views.register, name='register'),
    path('connexion/', views.login_view, name='login'),
    path('deconnexion/', views.logout_view, name='logout'),

    # Espace parent
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profil/', views.profil, name='profil'),
    path('profil/edit/', views.profile_edit, name='profile_edit'),
    path('profil/enfant/ajouter/', views.ajouter_enfant, name='ajouter_enfant'),

    # Vérification téléphone (OTP)
    path('phone/send/', views.send_phone_otp, name='phone_send'),
    path('phone/verify/', views.verify_phone_otp, name='phone_verify'),
]
