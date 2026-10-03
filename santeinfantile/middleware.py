"""En-têtes de sécurité applicatifs.

Django pose déjà `X-Content-Type-Options`, `Referrer-Policy`,
`X-Frame-Options`, `Strict-Transport-Security` et
`Cross-Origin-Opener-Policy` via `SecurityMiddleware` et les réglages de
`settings.py`. Restent deux en-têtes qu'il n'écrit pas : la
Content-Security-Policy et la Permissions-Policy. C'est le rôle de ce module.

Note sur `'unsafe-inline'` : le site utilise de nombreux scripts et styles
en ligne (cartes Leaflet, bandeaux, menus). Les interdire casserait les pages.
La CSP reste néanmoins utile : elle verrouille `default-src`, interdit les
plugins (`object-src 'none'`), empêche l'inclusion du site dans une iframe
tierce (`frame-ancestors`) et restreint les destinations de formulaire.
"""

# Origines externes réellement utilisées par le site.
# Leaflet est auto-hébergé dans /static/vendor/ : unpkg.com n'est plus autorisé.
CDN_SCRIPTS = "https://cdn.jsdelivr.net"
CDN_STYLES = "https://cdn.jsdelivr.net https://fonts.googleapis.com"
CDN_POLICES = "https://fonts.gstatic.com"
TUILES_CARTE = "https://tile.openstreetmap.org https://*.tile.openstreetmap.org"

def _frame_ancestors():
    """Origines autorisées à embarquer le site dans une iframe.

    Vaut `'self'` en production. Le réglage reste configurable pour les
    environnements d'aperçu (bacs à sable, recette) qui affichent le site dans
    une iframe d'un autre domaine.
    """
    from django.conf import settings

    return getattr(settings, 'CSP_FRAME_ANCESTORS', "'self'")


CSP_BASE = "; ".join([
    "default-src 'self'",
    f"script-src 'self' 'unsafe-inline' {CDN_SCRIPTS}",
    f"style-src 'self' 'unsafe-inline' {CDN_STYLES}",
    f"font-src 'self' data: {CDN_POLICES}",
    f"img-src 'self' data: blob: {TUILES_CARTE}",
    "connect-src 'self' https://overpass-api.de",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "manifest-src 'self'",
    "worker-src 'self'",
])

# Fonctionnalités du navigateur : on n'autorise que la géolocalisation
# (bouton « Me localiser » de la carte), tout le reste est refusé.
PERMISSIONS_POLICY = ", ".join([
    "geolocation=(self)",
    "camera=()",
    "microphone=()",
    "payment=()",
    "usb=()",
    "magnetometer=()",
    "gyroscope=()",
    "accelerometer=()",
    "interest-cohort=()",
])


class SecurityHeadersMiddleware:
    """Ajoute la CSP et la Permissions-Policy à chaque réponse."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.csp = f"{CSP_BASE}; frame-ancestors {_frame_ancestors()}"

    def __call__(self, request):
        reponse = self.get_response(request)
        reponse.setdefault('Content-Security-Policy', self.csp)
        reponse.setdefault('Permissions-Policy', PERMISSIONS_POLICY)
        # Empêche Internet Explorer d'ouvrir un téléchargement dans le contexte
        # du site (toujours recommandé par l'OWASP, coût nul).
        reponse.setdefault('X-Download-Options', 'noopen')
        return reponse
