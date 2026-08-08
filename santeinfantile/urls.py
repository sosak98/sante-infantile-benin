from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # assume accounts.urls gère login, profile_edit, dashboard...
    path('', include('main.urls')),  # page d'accueil route ou patterns existants
]

# Si vos routes d'accounts n'incluent pas /a-propos/, vous pouvez ajouter ici :
# from accounts import views as accounts_views
# urlpatterns += [ path('a-propos/', accounts_views.about, name='a_propos') ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
