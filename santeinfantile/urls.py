from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', accounts_views.accueil, name='accueil'),
    path('gestion-sib-secure-2026/', admin.site.urls),
    path('register/', accounts_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', accounts_views.dashboard, name='dashboard'),
    path('profil/', accounts_views.profil, name='profil'),
    path('profil/ajouter-enfant/', accounts_views.ajouter_enfant, name='ajouter_enfant'),
    path('carte/', include('sante.urls')),
    path('vaccination/', include('conseils.urls')),
    path('malnutrition/', include('enfants.urls')),
    path('conseils/', include('conseils.urls')),
    path('sib-intelligence/', include('sib_intelligence.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
