from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', accounts_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', accounts_views.dashboard, name='dashboard'),
    path('carte/', include('sante.urls')),
    path('vaccination/', include('conseils.urls')),
    path('malnutrition/', include('enfants.urls')),
    path('conseils/', include('conseils.urls')),
]
