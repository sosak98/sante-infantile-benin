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


# Version du cache. À incrémenter à CHAQUE changement du service worker ou de
# la liste CORE : c'est ce qui déclenche la purge des anciens caches chez les
# visiteurs qui ont déjà installé l'application.
SW_VERSION = 'v9'

# Pages pré-mises en cache dès l'installation : tous les modules utiles hors
# ligne, y compris les nouvelles pages « jours de vaccination » et l'espace
# professionnels.
PAGES_HORS_LIGNE = [
    '/',
    '/hors-ligne/',
    '/carte/',
    '/carte/vaccination/',
    '/depistage/',
    '/conseils/',
    '/conseils/rdv/',
    '/conseils/nutrition/',
    '/premiers-secours/',
    '/pro/',
    '/a-propos/',
    '/cgu/',
    '/politique-de-confidentialite/',
    '/politique-des-cookies/',
]

STATIQUES_HORS_LIGNE = [
    '/static/css/sib.css',
    '/static/img/logo.png',
    '/static/img/icons/icon-192.png',
    '/static/img/icons/icon-512.png',
    '/static/img/icons/apple-touch-icon.png',
    '/manifest.json',
]


def _liste_js(valeurs):
    return ',\n  '.join("'%s'" % v for v in valeurs)


SW_JS = """
// Santé Infantile Bénin : Service Worker (PWA, mode hors-ligne étendu)
//
// Stratégies :
//   navigation   -> réseau d'abord, repli sur la page en cache puis /hors-ligne/
//   /static/     -> cache d'abord + rafraîchissement en arrière-plan (rapide)
//   CDN          -> cache d'abord + rafraîchissement en arrière-plan
//   autres GET   -> réseau seul (jamais de mise en cache d'API)
const VERSION = '%(version)s';
const CACHE = 'sib-cache-' + VERSION;
const OFFLINE = '/hors-ligne/';
const MAX_ITEMS = 250;

// Pages disponibles hors ligne dès l'installation.
const CORE = [
  %(pages)s
];

const STATIQUES = [
  %(statiques)s
];

// CDN utilisés par le site (Bootstrap, Leaflet, polices) : mis en cache aussi.
const CDN_HOSTS = ['cdn.jsdelivr.net', 'unpkg.com', 'fonts.googleapis.com',
                   'fonts.gstatic.com'];
const CDN_CORE = [
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then(async (cache) => {
        // Chaque ressource est tentée individuellement : une indisponibilité
        // ponctuelle ne doit pas empêcher l'installation du service worker.
        await Promise.allSettled(CORE.map((url) => cache.add(url)));
        await Promise.allSettled(STATIQUES.map((url) => cache.add(url)));
        await Promise.allSettled(CDN_CORE.map((url) => cache.add(url)));
      })
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
  e.waitUntil((async () => {
    // Purge de toutes les versions precedentes du cache.
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
    if (self.registration.navigationPreload) {
      try { await self.registration.navigationPreload.enable(); } catch (err) { /* ignore */ }
    }
    await trimCache(CACHE);
    await self.clients.claim();
  })());
});

// Permet a la page de demander l'activation immediate d'une nouvelle version.
self.addEventListener('message', (e) => {
  if (e.data === 'SKIP_WAITING') self.skipWaiting();
  if (e.data === 'VERSION' && e.source) e.source.postMessage({ version: VERSION });
});

// Cache d'abord, puis rafraichissement silencieux en arriere-plan.
async function cacheAbordPuisReseau(request) {
  const cache = await caches.open(CACHE);
  const cached = await cache.match(request);
  const reseau = fetch(request).then((res) => {
    if (res && res.ok) {
      cache.put(request, res.clone());
      trimCache(CACHE);
    }
    return res;
  }).catch(() => null);
  return cached || (await reseau) || Response.error();
}

self.addEventListener('fetch', (e) => {
  const { request } = e;
  if (request.method !== 'GET') return;

  let url;
  try { url = new URL(request.url); } catch (err) { return; }
  if (!url.protocol.startsWith('http')) return;

  // Jamais de cache sur l'administration ni les appels de donnees vivants.
  if (url.origin === self.location.origin &&
      (url.pathname.startsWith('/admin/') ||
       url.pathname.startsWith('/triage/chat') ||
       url.pathname.startsWith('/carte/osm'))) {
    return;
  }

  // Navigations : reseau d'abord, puis cache de la page, puis page hors-ligne.
  if (request.mode === 'navigate') {
    e.respondWith((async () => {
      try {
        const preload = e.preloadResponse ? await e.preloadResponse : null;
        const res = preload || await fetch(request);
        if (res && res.ok && url.origin === self.location.origin) {
          const cache = await caches.open(CACHE);
          cache.put(request, res.clone());
          trimCache(CACHE);
        }
        return res;
      } catch (err) {
        return (await caches.match(request))
          || (await caches.match(OFFLINE))
          || (await caches.match('/'))
          || new Response('Hors ligne', { status: 503, statusText: 'Hors ligne' });
      }
    })());
    return;
  }

  // Fichiers statiques du site : cache d'abord (affichage instantane hors ligne).
  if (url.origin === self.location.origin &&
      (url.pathname.startsWith('/static/') || url.pathname === '/manifest.json')) {
    e.respondWith(cacheAbordPuisReseau(request));
    return;
  }

  // CDN (Bootstrap, Leaflet, polices) : cache d'abord egalement.
  if (CDN_HOSTS.includes(url.hostname)) {
    e.respondWith(cacheAbordPuisReseau(request));
  }
});
""" % {
    'version': SW_VERSION,
    'pages': _liste_js(PAGES_HORS_LIGNE),
    'statiques': _liste_js(STATIQUES_HORS_LIGNE),
}


@require_GET
def service_worker(request):
    reponse = HttpResponse(SW_JS, content_type='application/javascript')
    # Le service worker ne doit jamais être servi depuis un cache HTTP périmé,
    # sinon une nouvelle version ne serait jamais activée chez les visiteurs.
    reponse['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    reponse['Service-Worker-Allowed'] = '/'
    return reponse
