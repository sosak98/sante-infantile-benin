from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('a-propos/', views.about, name='a_propos'),  # si vous préférez ici
    path('profile/edit/', views.profile_edit, name='profile_edit'),  # exemple attendu pour le lien
    # ... autres routes ...
]
