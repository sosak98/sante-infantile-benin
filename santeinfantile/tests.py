"""Tests de bout en bout : toutes les routes publiques doivent répondre en 200,
les fichiers d'indexation IA (llms.txt), les bandeaux PWA/cookies et les
données structurées Schema.org doivent être présents."""
from django.test import TestCase

# Toutes les routes publiques du site (GET, sans authentification)
ROUTES_PUBLIQUES = [
    '/',
    '/a-propos/',
    '/carte/',
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
