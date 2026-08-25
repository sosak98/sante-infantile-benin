"""Vues PWA : manifeste et service worker, servis à la racine du domaine."""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.templatetags.static import static


@require_GET
def manifest(request):
    base = request.build_absolute_uri('/')[:-1]

    def full(path):
        return request.build_absolute_uri(static(path))

    data = {
        'name': 'Santé Infantile Bénin',
        'short_name': 'Santé Enfant',
        'description': (
            'Plateforme de suivi de la santé des nourrissons et jeunes enfants au Bénin : '
            'vaccination, nutrition, dépistage de la malnutrition et triage pédiatrique assisté par IA.'
        ),
        'lang': 'fr',
        'start_url': base + '/',
        'scope': base + '/',
        'display': 'standalone',
        'orientation': 'portrait',
        'background_color': '#ffffff',
        'theme_color': '#ffffff',
        'icons': [
            {'src': full('img/icons/icon-192.png'), 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': full('img/icons/icon-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': full('img/icons/icon-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    }
    return JsonResponse(data)


SW_JS = """
// Santé Infantile Bénin — Service Worker (PWA)
const CACHE = 'sib-cache-v4';
const CORE = [
  '/',
  '/static/css/sib.css',
  '/static/img/logo.png',
  '/static/img/icons/icon-192.png',
  '/static/img/icons/icon-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const { request } = e;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  // Navigation : réseau d'abord, cache en secours (mode hors-ligne)
  if (request.mode === 'navigate') {
    e.respondWith(
      fetch(request)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put('/', copy));
          return res;
        })
        .catch(() => caches.match('/'))
    );
    return;
  }

  // Assets statiques : cache d'abord
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(
      caches.match(request).then(
        (cached) => cached || fetch(request).then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(request, copy));
          return res;
        })
      )
    );
  }
});
"""


@require_GET
def service_worker(request):
    return HttpResponse(SW_JS, content_type='application/javascript')
