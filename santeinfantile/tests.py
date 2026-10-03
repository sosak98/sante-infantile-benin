"""Tests de bout en bout : toutes les routes publiques doivent répondre en 200,
les fichiers d'indexation IA (llms.txt), les bandeaux PWA/cookies et les
données structurées Schema.org doivent être présents."""
from django.test import TestCase

# Toutes les routes publiques du site (GET, sans authentification)
ROUTES_PUBLIQUES = [
    '/',
    '/a-propos/',
    '/carte/',
    '/carte/vaccination/',
    '/pro/',
    '/pro/inscription/',
    '/depistage/',
    '/conseils/',
    '/conseils/rdv/',
    '/conseils/nutrition/',
    '/premiers-secours/',
    '/triage/',
    '/inscription/',
    '/connexion/',
    '/politique-de-confidentialite/',
    '/politique-des-cookies/',
    '/cgu/',
    '/hors-ligne/',
    '/robots.txt',
    '/sitemap.xml',
    '/llms.txt',
    '/llms-full.txt',
    '/manifest.json',
    '/sw.js',
]


class RoutesPubliquesTests(TestCase):
    """Chaque route publique doit répondre 200."""

    def test_toutes_les_routes_repondent_200(self):
        erreurs = []
        for route in ROUTES_PUBLIQUES:
            with self.subTest(route=route):
                reponse = self.client.get(route)
                if reponse.status_code != 200:
                    erreurs.append((route, reponse.status_code))
        self.assertEqual(erreurs, [])

    def test_zones_privees_protegees(self):
        """Les zones privées redirigent vers la connexion (302), jamais de 200 anonyme."""
        for route in ['/dashboard/', '/profil/']:
            with self.subTest(route=route):
                reponse = self.client.get(route)
                self.assertEqual(reponse.status_code, 302)


class IndexationIATests(TestCase):
    """/llms.txt, /llms-full.txt et robots.txt pour les assistants IA."""

    def test_llms_txt_format(self):
        reponse = self.client.get('/llms.txt')
        self.assertEqual(reponse.status_code, 200)
        texte = reponse.content.decode('utf-8')
        self.assertTrue(texte.startswith('# Santé Infantile Bénin'))
        self.assertIn('> Plateforme web gratuite', texte)  # bloc citation (résumé)
        self.assertIn('/premiers-secours/', texte)
        self.assertIn('/conseils/nutrition/', texte)
        self.assertIn('/politique-des-cookies/', texte)
        self.assertIn('112', texte)

    def test_llms_full_txt_contenu(self):
        reponse = self.client.get('/llms-full.txt')
        self.assertEqual(reponse.status_code, 200)
        texte = reponse.content.decode('utf-8')
        # Les modules attendus sont documentés
        for attendu in ['PEV', 'Pentavalent', 'Z-scores', 'MUAC', 'premiers secours',
                        'Politique des cookies', 'APDP', '118', '117']:
            with self.subTest(attendu=attendu):
                self.assertIn(attendu, texte)

    def test_robots_txt_autorise_bots_ia_et_bloque_prive(self):
        reponse = self.client.get('/robots.txt')
        self.assertEqual(reponse.status_code, 200)
        texte = reponse.content.decode('utf-8')
        # Bots IA explicitement autorisés
        for bot in ['GPTBot', 'ClaudeBot', 'PerplexityBot', 'Google-Extended']:
            with self.subTest(bot=bot):
                self.assertIn(f'User-agent: {bot}', texte)
        # Zones privées interdites à tous
        for zone in ['/admin/', '/dashboard/', '/profil/', '/triage/chat/']:
            with self.subTest(zone=zone):
                self.assertIn(f'Disallow: {zone}', texte)
        self.assertIn('Sitemap:', texte)
        self.assertIn('/llms.txt', texte)

    def test_sitemap_inclut_nouvelles_pages(self):
        reponse = self.client.get('/sitemap.xml')
        self.assertEqual(reponse.status_code, 200)
        xml = reponse.content.decode('utf-8')
        self.assertIn('/politique-des-cookies/', xml)
        self.assertIn('/conseils/nutrition/', xml)
        # Les zones privées n'y figurent pas
        self.assertNotIn('/dashboard/', xml)
        self.assertNotIn('/admin/', xml)


class PWAEtBandeauxTests(TestCase):
    """Bandeau d'installation PWA, bandeau cookies, données structurées."""

    def test_page_inclut_bandeau_pwa_et_cookies(self):
        reponse = self.client.get('/')
        self.assertEqual(reponse.status_code, 200)
        html = reponse.content.decode('utf-8')
        self.assertIn('id="pwaBanner"', html)
        self.assertIn('beforeinstallprompt', html)
        self.assertIn('id="cookieBanner"', html)
        self.assertIn('id="cookieOk"', html)
        self.assertIn('Compris', html)

    def test_page_hors_ligne_est_un_hub_complet(self):
        reponse = self.client.get('/hors-ligne/')
        self.assertEqual(reponse.status_code, 200)
        html = reponse.content.decode('utf-8')
        # Accès direct à tous les outils + rappel 112
        self.assertIn('/conseils/', html)          # vaccination PEV
        self.assertIn('/conseils/nutrition/', html)  # nutrition
        self.assertIn('/depistage/', html)         # Z-scores
        self.assertIn('/premiers-secours/', html)  # SOS
        self.assertIn('/carte/', html)             # carte des structures
        self.assertIn('112', html)
        self.assertIn('tel:112', html)

    def test_service_worker_precache_tous_les_modules(self):
        reponse = self.client.get('/sw.js')
        self.assertEqual(reponse.status_code, 200)
        sw = reponse.content.decode('utf-8')
        for module in ["'/carte/'", "'/depistage/'", "'/conseils/'",
                       "'/conseils/nutrition/'", "'/premiers-secours/'"]:
            with self.subTest(module=module):
                self.assertIn(module, sw)

    def test_manifest_json_valide(self):
        reponse = self.client.get('/manifest.json')
        self.assertEqual(reponse.status_code, 200)
        data = reponse.json()
        self.assertEqual(data['name'], 'Santé Infantile Bénin')
        self.assertEqual(data['display'], 'standalone')
        self.assertTrue(len(data['icons']) >= 2)


class DonneesStructureesTests(TestCase):
    """JSON-LD Schema.org : MedicalOrganization et EmergencyService 112."""

    def test_accueil_contient_json_ld(self):
        reponse = self.client.get('/')
        self.assertEqual(reponse.status_code, 200)
        html = reponse.content.decode('utf-8')
        self.assertIn('application/ld+json', html)
        self.assertIn('MedicalOrganization', html)
        self.assertIn('EmergencyService', html)
        self.assertIn('"telephone": "112"', html)


class EnTeteTests(TestCase):
    """Boutons d'en-tête harmonisés « Inscription » / « Connexion »."""

    def test_boutons_en_tete_harmonises(self):
        reponse = self.client.get('/')
        html = reponse.content.decode('utf-8')
        self.assertIn('>Connexion</a>', html)
        self.assertIn('>Inscription</a>', html)
        self.assertNotIn('Créer un compte', html)

    def test_lien_politique_cookies_partout(self):
        for route in ['/', '/politique-de-confidentialite/']:
            with self.subTest(route=route):
                reponse = self.client.get(route)
                html = reponse.content.decode('utf-8')
                self.assertIn('/politique-des-cookies/', html)


class EnTetesSecuriteTests(TestCase):
    """Audit sécurité : en-têtes présents sur toutes les réponses."""

    def test_csp_presente_et_verrouillee(self):
        reponse = self.client.get('/')
        csp = reponse.headers.get('Content-Security-Policy', '')
        self.assertIn("default-src 'self'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("base-uri 'self'", csp)
        self.assertIn("form-action 'self'", csp)
        self.assertIn("frame-ancestors 'self'", csp)

    def test_csp_autorise_les_cdn_reellement_utilises(self):
        csp = self.client.get('/').headers.get('Content-Security-Policy', '')
        for origine in ['https://cdn.jsdelivr.net',
                        'https://fonts.googleapis.com', 'https://fonts.gstatic.com']:
            with self.subTest(origine=origine):
                self.assertIn(origine, csp)
        # Leaflet est auto-hébergé : unpkg.com ne doit plus être autorisé.
        self.assertNotIn('unpkg.com', csp)

    def test_csp_autorise_les_tuiles_de_carte(self):
        csp = self.client.get('/carte/').headers.get('Content-Security-Policy', '')
        self.assertIn('tile.openstreetmap.org', csp)
        self.assertIn('basemaps.cartocdn.com', csp)

    def test_permissions_policy_restrictive(self):
        entete = self.client.get('/').headers.get('Permissions-Policy', '')
        self.assertIn('geolocation=(self)', entete)
        for interdit in ['camera=()', 'microphone=()', 'payment=()']:
            with self.subTest(interdit=interdit):
                self.assertIn(interdit, entete)

    def test_entetes_django_standards(self):
        reponse = self.client.get('/')
        self.assertEqual(reponse.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(reponse.headers.get('Referrer-Policy'),
                         'strict-origin-when-cross-origin')
        self.assertEqual(reponse.headers.get('X-Frame-Options'), 'SAMEORIGIN')

    def test_entetes_sur_toutes_les_pages_publiques(self):
        for route in ['/', '/carte/', '/conseils/', '/carte/vaccination/', '/pro/']:
            with self.subTest(route=route):
                reponse = self.client.get(route)
                self.assertIn('Content-Security-Policy', reponse.headers)
                self.assertIn('Permissions-Policy', reponse.headers)

    def test_cookies_securises_en_configuration(self):
        from django.conf import settings
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, 'Lax')
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, 'Lax')
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)

    def test_module_ia_optionnel_ne_casse_pas_le_site(self):
        """Sans clé Groq, le triage doit répondre, pas planter."""
        self.assertEqual(self.client.get('/triage/').status_code, 200)


class ServiceWorkerV12Tests(TestCase):
    """Mode hors-ligne étendu : version du cache et pages pré-enregistrées."""

    def test_version_v12(self):
        sw = self.client.get('/sw.js').content.decode('utf-8')
        self.assertIn("const VERSION = 'v12'", sw)
        self.assertIn("'sib-cache-' + VERSION", sw)

    def test_nouvelles_pages_precachees(self):
        sw = self.client.get('/sw.js').content.decode('utf-8')
        for page in ["'/carte/vaccination/'", "'/conseils/rdv/'", "'/pro/'",
                     "'/premiers-secours/'", "'/hors-ligne/'"]:
            with self.subTest(page=page):
                self.assertIn(page, sw)

    def test_zones_jamais_mises_en_cache(self):
        sw = self.client.get('/sw.js').content.decode('utf-8')
        for zone in ["'/admin/'", "'/triage/chat'", "'/carte/osm'"]:
            with self.subTest(zone=zone):
                self.assertIn(zone, sw)

    def test_service_worker_non_cachable_par_le_navigateur(self):
        reponse = self.client.get('/sw.js')
        self.assertIn('no-cache', reponse.headers.get('Cache-Control', ''))
        self.assertEqual(reponse.headers.get('Service-Worker-Allowed'), '/')

    def test_purge_des_anciennes_versions(self):
        sw = self.client.get('/sw.js').content.decode('utf-8')
        self.assertIn('caches.delete', sw)
        self.assertIn('navigationPreload', sw)

    def test_page_hors_ligne_liste_les_nouveaux_outils(self):
        html = self.client.get('/hors-ligne/').content.decode('utf-8')
        self.assertIn('/carte/vaccination/', html)
        self.assertIn('/conseils/rdv/', html)


class LeafletAutoHeberge(TestCase):
    """Leaflet et MarkerCluster servis depuis /static/vendor/, plus aucun CDN.

    Cause : unpkg.com est injoignable depuis certaines connexions béninoises ;
    la carte restait blanche et les compteurs affichaient zéro.
    """

    CHEMINS_VENDOR = [
        'vendor/leaflet/leaflet.css',
        'vendor/leaflet/leaflet.js',
        'vendor/markercluster/MarkerCluster.css',
        'vendor/markercluster/MarkerCluster.Default.css',
        'vendor/markercluster/leaflet.markercluster.js',
    ]

    def test_carte_sans_aucun_cdn(self):
        html = self.client.get('/carte/').content.decode('utf-8')
        self.assertNotIn('unpkg.com', html)
        self.assertNotIn('unpkg', html)

    def test_carte_reference_les_fichiers_locaux(self):
        html = self.client.get('/carte/').content.decode('utf-8')
        for chemin in self.CHEMINS_VENDOR:
            with self.subTest(chemin=chemin):
                self.assertIn('/static/' + chemin, html)

    def test_fichiers_vendor_reellement_presents_sur_le_disque(self):
        """Un chemin correct dans le HTML ne prouve rien si le fichier manque."""
        from django.contrib.staticfiles import finders
        fichiers = self.CHEMINS_VENDOR + ['vendor/leaflet/images/marker-icon.png',
                                          'vendor/leaflet/images/marker-shadow.png']
        for chemin in fichiers:
            with self.subTest(chemin=chemin):
                self.assertIsNotNone(finders.find(chemin),
                                     'Fichier introuvable : %s' % chemin)

    def test_service_worker_precache_leaflet_sans_unpkg(self):
        sw = self.client.get('/sw.js').content.decode('utf-8')
        for chemin in self.CHEMINS_VENDOR:
            with self.subTest(chemin=chemin):
                self.assertIn("'/static/" + chemin + "'", sw)
        self.assertNotIn('unpkg', sw)


class PagesErreurTests(TestCase):
    """Page 404 en français, utile plutôt que nue."""

    def test_404_est_en_francais_et_orientee(self):
        reponse = self.client.get('/cette-page-nexiste-pas/')
        self.assertEqual(reponse.status_code, 404)
        html = reponse.content.decode('utf-8')
        self.assertIn('Page introuvable', html)
        self.assertIn('112', html)

    def test_404_propose_les_outils_principaux(self):
        html = self.client.get('/url-inconnue/').content.decode('utf-8')
        for lien in ['/conseils/', '/carte/vaccination/', '/depistage/',
                     '/premiers-secours/']:
            with self.subTest(lien=lien):
                self.assertIn(lien, html)

    def test_404_utilise_bien_le_gabarit_du_site(self):
        html = self.client.get('/autre-url-inconnue/').content.decode('utf-8')
        self.assertIn('Santé Infantile Bénin', html)


class NavigationTests(TestCase):
    """Les nouvelles pages sont atteignables depuis toutes les pages."""

    def test_barre_de_navigation_sans_jours_de_vaccin(self):
        """L'entrée « Jours de vaccin » quittait la barre (8 entrées débordaient
        sur téléphone) ; le lien reste dans le calendrier et le pied de page."""
        html = self.client.get('/').content.decode('utf-8')
        self.assertNotIn('>Jours de vaccin</a>', html)

    def test_calendrier_relaie_les_jours_de_vaccination(self):
        reponse = self.client.get('/conseils/')
        self.assertContains(reponse, 'Jours de vaccination par centre')
        self.assertContains(reponse, '/carte/vaccination/')

    def test_menu_expose_les_jours_de_vaccination(self):
        self.assertContains(self.client.get('/'), '/carte/vaccination/')

    def test_pied_de_page_expose_l_espace_pro(self):
        self.assertContains(self.client.get('/'), '/pro/')

    def test_sitemap_inclut_les_nouvelles_pages(self):
        xml = self.client.get('/sitemap.xml').content.decode('utf-8')
        self.assertIn('/carte/vaccination/', xml)
        self.assertIn('/pro/', xml)

    def test_robots_protege_les_zones_pro(self):
        txt = self.client.get('/robots.txt').content.decode('utf-8')
        for zone in ['/pro/tableau-de-bord/', '/pro/mon-centre/']:
            with self.subTest(zone=zone):
                self.assertIn(f'Disallow: {zone}', txt)

    def test_llms_full_contient_le_calendrier_corrige(self):
        txt = self.client.get('/llms-full.txt').content.decode('utf-8')
        self.assertIn('Rotavirus 1', txt)
        self.assertIn('VPI (polio injectable)', txt)
        self.assertIn('Antipaludique 1 (RTS,S)', txt)
        # L'ancien texte annonçait à tort « RTSS (rotavirus) » à 22 semaines.
        self.assertNotIn('RTSS (rotavirus)', txt)
        self.assertNotIn('À partir de 22 semaines', txt)
