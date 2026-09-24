"""Vues PWA : manifeste, service worker (mode hors ligne) et page hors-ligne."""
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.templatetags.static import static


@require_GET
def manifest(request):
    base = request.build_absolute_uri('/')[:-1]

    def full(path):
        return request.build_absolute_uri(static(path))

    data = {
        'id': base + '/',
        'name': 'Santé Infantile Bénin',
        'short_name': 'Santé Enfant',
        'description': (
            'Plateforme de suivi de la santé des nourrissons et jeunes enfants au Bénin : '
            'vaccination, nutrition, dépistage de la malnutrition, premiers secours et triage pédiatrique.'
        ),
        'lang': 'fr',
        'start_url': base + '/',
        'scope': base + '/',
        'display': 'standalone',
        'orientation': 'portrait',
        'background_color': '#ffffff',
        'theme_color': '#00695c',
        'categories': ['health', 'medical', 'lifestyle'],
        'icons': [
            {'src': full('img/icons/icon-192.png'), 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': full('img/icons/icon-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': full('img/icons/icon-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    }
    return JsonResponse(data)


def hors_ligne(request):
    """Page de repli affichée par le service worker quand il n'y a pas de réseau."""
    return render(request, 'hors_ligne.html')


SW_JS = """
// Santé Infantile Bénin : Service Worker (PWA, mode hors-ligne)
const CACHE = 'sib-cache-v6';
const OFFLINE = '/hors-ligne/';
const MAX_ITEMS = 120;

// Ressources essentielles pré-mises en cache dès l'installation
const CORE = [
  '/',
  OFFLINE,
  '/static/css/sib.css',
  '/static/img/logo.png',
  '/static/img/icons/icon-192.png',
  '/static/img/icons/icon-512.png',
];

// CDN utilisés par le site (Bootstrap, Leaflet...) : mis en cache pour le hors-ligne
const CDN_HOSTS = ['cdn.jsdelivr.net', 'unpkg.com', 'fonts.googleapis.com', 'fonts.gstatic.com'];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => c.addAll(CORE))
      .then(() => self.skipWaiting())
  );
});

async function trimCache(name) {
  try {
    const cache = await caches.open(name);
    const keys = await cache.keys();
    if (keys.length > MAX_ITEMS) {
      await cache.delete(keys[0]);
      await trimCache(name);
    }
  } catch (err) { /* nettoyage best-effort */ }
}

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => trimCache(CACHE))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const { request } = e;
  if (request.method !== 'GET') return;

  let url;
  try { url = new URL(request.url); } catch (err) { return; }
  if (!url.protocol.startsWith('http')) return;

  // Navigations : réseau d'abord, puis cache de la page, puis accueil, puis page hors-ligne
  if (request.mode === 'navigate') {
    e.respondWith((async () => {
      try {
        const res = await fetch(request);
        if (res && res.ok && url.origin === self.location.origin) {
          const cache = await caches.open(CACHE);
          cache.put(request, res.clone());
          trimCache(CACHE);
        }
        return res;
      } catch (err) {
        return (await caches.match(request))
          || (await caches.match('/'))
          || (await caches.match(OFFLINE));
      }
    })());
    return;
  }

  // Fichiers statiques du site : réseau d'abord (pour voir les nouveautés),
  // cache en secours (pour le mode hors-ligne)
  if (url.origin === self.location.origin && url.pathname.startsWith('/static/')) {
    e.respondWith((async () => {
      const cache = await caches.open(CACHE);
      try {
        const res = await fetch(request);
        if (res && res.ok) {
          cache.put(request, res.clone());
          trimCache(CACHE);
        }
        return res;
      } catch (err) {
        const cached = await cache.match(request);
        return cached || Response.error();
      }
    })());
    return;
  }

  // CDN (Bootstrap, Leaflet) : réseau d'abord, cache en secours
  if (CDN_HOSTS.includes(url.hostname)) {
    e.respondWith((async () => {
      try {
        const res = await fetch(request);
        if (res && res.ok) {
          const cache = await caches.open(CACHE);
          cache.put(request, res.clone());
        }
        return res;
      } catch (err) {
        const cached = await caches.match(request);
        return cached || Response.error();
      }
    })());
  }
});
"""


@require_GET
def service_worker(request):
    return HttpResponse(SW_JS, content_type='application/javascript')
