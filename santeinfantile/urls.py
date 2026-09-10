from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import pwa, seo

from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),

    # PWA
    path('robots.txt', seo.robots_txt, name='robots_txt'),
    path('sitemap.xml', seo.sitemap_xml, name='sitemap_xml'),
    path('manifest.json', pwa.manifest, name='manifest'),
    path('sw.js', pwa.service_worker, name='service_worker'),

    # Pages (l'accueil vit dans l'app accounts, à la racine)
    path('', include('accounts.urls')),

    # Modules
    path('carte/', include('sante.urls')),
    path('depistage/', include('enfants.urls')),
    path('conseils/', include('conseils.urls')),
    path('triage/', include('sib_intelligence.urls')),

    # Photos profil (Render n'a pas DEBUG=True)
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]
