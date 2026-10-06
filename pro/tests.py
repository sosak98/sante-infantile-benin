"""Tests de l'espace professionnels de santé.

L'essentiel porte sur le contrôle d'accès : un compte non validé ne doit
pouvoir modifier aucune information publique d'un centre de santé.
"""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from pro.admin import ProfessionnelSanteAdmin
from pro.models import ProfessionnelSante
from sante.models import Etablissement


def creer_centre(nom='CS de Test'):
    return Etablissement.objects.create(
        nom=nom, type_etab='centre', adresse='Cotonou, Bénin',
        commune='Cotonou', latitude=6.37, longitude=2.41,
        fait_vaccination=True,
    )


def creer_pro(statut='valide', etablissement=None, identifiant='agent@test.bj'):
    user = User.objects.create_user(
        username=identifiant, email=identifiant, password='MotDePasse123',
        first_name='Awa', last_name='Koffi',
    )
    return ProfessionnelSante.objects.create(
        user=user, fonction='infirmier', etablissement=etablissement,
        telephone='97000000', statut=statut,
    )


class AccesEspaceProTests(TestCase):

    def test_accueil_pro_est_public(self):
        reponse = self.client.get('/pro/')
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'professionnels de santé')

    def test_accueil_pro_sans_centre_publie_evite_le_zero(self):
        """« 0 centres publient déjà ses jours » est du mauvais français."""
        reponse = self.client.get('/pro/')
        self.assertEqual(reponse.context['centres_publies'], 0)
        self.assertContains(reponse, 'Soyez le premier centre')
        self.assertNotContains(reponse, '0 centre')

    def test_inscription_accessible(self):
        self.assertEqual(self.client.get('/pro/inscription/').status_code, 200)

    def test_tableau_de_bord_refuse_aux_anonymes(self):
        reponse = self.client.get('/pro/tableau-de-bord/')
        self.assertEqual(reponse.status_code, 302)
        self.assertIn('/connexion/', reponse.url)

    def test_fiche_centre_refusee_aux_anonymes(self):
        reponse = self.client.get('/pro/mon-centre/')
        self.assertEqual(reponse.status_code, 302)

    def test_utilisateur_sans_profil_pro_est_redirige(self):
        User.objects.create_user(username='parent@test.bj', password='MotDePasse123')
        self.client.login(username='parent@test.bj', password='MotDePasse123')
        reponse = self.client.get('/pro/tableau-de-bord/')
        self.assertRedirects(reponse, '/pro/')

    def test_compte_en_attente_bloque_sur_la_page_d_attente(self):
        creer_pro(statut='en_attente')
        self.client.login(username='agent@test.bj', password='MotDePasse123')
        self.assertRedirects(self.client.get('/pro/tableau-de-bord/'), '/pro/en-attente/')
        self.assertRedirects(self.client.get('/pro/mon-centre/'), '/pro/en-attente/')
        self.assertRedirects(self.client.get('/pro/outil-pev/'), '/pro/en-attente/')

    def test_compte_refuse_reste_bloque(self):
        creer_pro(statut='refuse')
        self.client.login(username='agent@test.bj', password='MotDePasse123')
        self.assertRedirects(self.client.get('/pro/tableau-de-bord/'), '/pro/en-attente/')

    def test_compte_valide_accede_au_tableau_de_bord(self):
        creer_pro(statut='valide', etablissement=creer_centre())
        self.client.login(username='agent@test.bj', password='MotDePasse123')
        reponse = self.client.get('/pro/tableau-de-bord/')
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'CS de Test')

    def test_compte_valide_redirige_depuis_accueil(self):
        creer_pro(statut='valide', etablissement=creer_centre())
        self.client.login(username='agent@test.bj', password='MotDePasse123')
        self.assertRedirects(self.client.get('/pro/'), '/pro/tableau-de-bord/')


class InscriptionProTests(TestCase):

    def donnees(self, **extra):
        valeurs = {
            'prenom': 'Awa', 'nom': 'Koffi',
            'email': 'awa@centre.bj', 'telephone': '97000000',
            'fonction': 'infirmier', 'structure_libre': 'CS Vedoko',
            'mot_de_passe': 'MotDePasse123', 'mot_de_passe2': 'MotDePasse123',
        }
        valeurs.update(extra)
        return valeurs

    def test_inscription_cree_un_compte_en_attente(self):
        reponse = self.client.post('/pro/inscription/', self.donnees())
        self.assertRedirects(reponse, '/pro/en-attente/')
        pro = ProfessionnelSante.objects.get(user__email='awa@centre.bj')
        self.assertEqual(pro.statut, 'en_attente')

    def test_inscription_refuse_les_mots_de_passe_differents(self):
        reponse = self.client.post(
            '/pro/inscription/', self.donnees(mot_de_passe2='Autre123456'))
        self.assertEqual(reponse.status_code, 200)
        self.assertFalse(ProfessionnelSante.objects.exists())

    def test_inscription_exige_une_structure(self):
        reponse = self.client.post('/pro/inscription/', self.donnees(structure_libre=''))
        self.assertEqual(reponse.status_code, 200)
        self.assertFalse(ProfessionnelSante.objects.exists())

    def test_inscription_refuse_un_email_deja_pris(self):
        User.objects.create_user(username='x', email='awa@centre.bj', password='y')
        reponse = self.client.post('/pro/inscription/', self.donnees())
        self.assertEqual(reponse.status_code, 200)
        self.assertFalse(ProfessionnelSante.objects.exists())


class DeclarationJoursTests(TestCase):

    def setUp(self):
        self.centre = creer_centre('CS Vedoko')
        self.pro = creer_pro(statut='valide', etablissement=self.centre)
        self.client.login(username='agent@test.bj', password='MotDePasse123')

    def test_publication_des_jours(self):
        reponse = self.client.post('/pro/mon-centre/', {
            'fait_vaccination': 'on',
            'jours': ['lundi', 'mercredi'],
            'horaire_vaccination': '08h00 - 12h00',
            'precision_vaccination': '',
            'telephone': '21300000',
            'commune': 'Cotonou',
        })
        self.assertRedirects(reponse, '/pro/mon-centre/')
        self.centre.refresh_from_db()
        self.assertEqual(self.centre.jours_liste, ['lundi', 'mercredi'])
        self.assertEqual(self.centre.source_vaccination, 'centre')
        self.assertIsNotNone(self.centre.maj_vaccination)

    def test_jours_publies_visibles_par_les_parents(self):
        self.client.post('/pro/mon-centre/', {
            'fait_vaccination': 'on', 'jours': ['lundi'],
            'horaire_vaccination': '09h00 - 13h00',
            'telephone': '', 'commune': 'Cotonou', 'precision_vaccination': '',
        })
        self.client.logout()
        reponse = self.client.get('/carte/vaccination/', {'jour': 'lundi'})
        self.assertContains(reponse, 'CS Vedoko')
        self.assertContains(reponse, '09h00 - 13h00')

    def test_vaccination_sans_jour_est_refusee(self):
        """Cocher « organise des séances » sans jour n'apporte rien au parent."""
        reponse = self.client.post('/pro/mon-centre/', {
            'fait_vaccination': 'on', 'jours': [],
            'horaire_vaccination': '', 'telephone': '',
            'commune': '', 'precision_vaccination': '',
        })
        self.assertEqual(reponse.status_code, 200)
        self.centre.refresh_from_db()
        self.assertEqual(self.centre.jours_liste, [])

    def test_un_agent_ne_modifie_que_son_centre(self):
        """L'agent n'a aucun moyen de désigner un autre établissement."""
        autre = creer_centre('CS Voisin')
        self.client.post('/pro/mon-centre/', {
            'fait_vaccination': 'on', 'jours': ['vendredi'],
            'horaire_vaccination': '', 'telephone': '',
            'commune': '', 'precision_vaccination': '',
            'id': autre.pk, 'etablissement': autre.pk,
        })
        autre.refresh_from_db()
        self.centre.refresh_from_db()
        self.assertEqual(autre.jours_liste, [])
        self.assertEqual(self.centre.jours_liste, ['vendredi'])

    def test_agent_sans_centre_est_redirige(self):
        pro = creer_pro(statut='valide', identifiant='sanscentre@test.bj')
        self.client.login(username='sanscentre@test.bj', password='MotDePasse123')
        self.assertRedirects(self.client.get('/pro/mon-centre/'), '/pro/tableau-de-bord/')


class OutilPevTests(TestCase):

    def setUp(self):
        creer_pro(statut='valide', etablissement=creer_centre())
        self.client.login(username='agent@test.bj', password='MotDePasse123')

    def test_planificateur_repond(self):
        self.assertEqual(self.client.get('/pro/outil-pev/').status_code, 200)

    def test_planificateur_calcule_un_planning(self):
        reponse = self.client.post('/pro/outil-pev/', {'date_naissance': '2025-01-15'})
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'Pentavalent 1')
        self.assertIsNotNone(reponse.context['resume'])

    def test_planificateur_tient_compte_des_doses_cochees(self):
        reponse = self.client.post('/pro/outil-pev/', {
            'date_naissance': '2025-01-15', 'recu': ['bcg', 'penta_1'],
        })
        self.assertEqual(reponse.context['resume']['recus'], 2)

    def test_planificateur_refuse_une_date_invalide(self):
        reponse = self.client.post('/pro/outil-pev/', {'date_naissance': 'oups'})
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'invalide')


class ModeleProTests(TestCase):

    def test_valider_change_le_statut(self):
        pro = creer_pro(statut='en_attente')
        self.assertFalse(pro.est_valide)
        pro.valider()
        pro.refresh_from_db()
        self.assertTrue(pro.est_valide)
        self.assertIsNotNone(pro.date_validation)

    def test_structure_affichee(self):
        centre = creer_centre('CS Akpakpa')
        self.assertEqual(creer_pro(etablissement=centre).structure_affichee, 'CS Akpakpa')
        pro = creer_pro(identifiant='b@test.bj')
        pro.structure_libre = 'Case de santé de Zè'
        self.assertEqual(pro.structure_affichee, 'Case de santé de Zè')


class InscriptionProTemplateTests(TestCase):

    def test_recherche_des_structures_est_presente(self):
        reponse = self.client.get('/pro/inscription/')
        self.assertContains(reponse, 'type="search"')
        self.assertContains(reponse, 'id="recherche_etablissement"')
        self.assertContains(reponse, 'optionsOriginales')
        self.assertContains(reponse, '.slice(0, 200)')
        self.assertContains(reponse, "setAttribute('size'")


class AdminProfessionnelTests(TestCase):

    def test_criteres_de_validation_documentes(self):
        criteres = ProfessionnelSanteAdmin.CRITERES_VALIDATION
        for attendu in (
            'fonction soignante', 'numéro d\'ordre ou matricule',
            'structure déclarée existe', 'adresse électronique est joignable',
            'Refuser plutôt que valider à moitié',
        ):
            with self.subTest(attendu=attendu):
                self.assertIn(attendu, criteres)

    def test_demandes_en_attente_affichees_en_premier(self):
        creer_pro(statut='valide', identifiant='valide@test.bj')
        creer_pro(statut='en_attente', identifiant='attente@test.bj')
        admin_instance = ProfessionnelSanteAdmin(ProfessionnelSante, None)
        demandes = admin_instance.get_queryset(None)
        self.assertEqual(demandes.first().statut, 'en_attente')


class AdditionalInscriptionProTemplateTests(TestCase):

    def test_recherche_est_placee_au_dessus_du_selecteur(self):
        html = self.client.get('/pro/inscription/').content.decode('utf-8')
        self.assertLess(
            html.index('id="recherche_etablissement"'),
            html.index('id="id_etablissement"'),
        )

    def test_filtre_conserve_les_options_originales(self):
        html = self.client.get('/pro/inscription/').content.decode('utf-8')
        self.assertIn('option.cloneNode(true)', html)
        self.assertIn('var optionsOriginales = null', html)

    def test_filtre_ne_depend_d_aucune_bibliotheque(self):
        html = self.client.get('/pro/inscription/').content.decode('utf-8')
        self.assertIn("addEventListener('input'", html)
        self.assertNotIn('jquery', html.lower())

    def test_resultats_du_filtre_sont_limites_a_deux_cents(self):
        html = self.client.get('/pro/inscription/').content.decode('utf-8')
        self.assertIn(".slice(0, 200)", html)


class SecuriteInscriptionProTests(TestCase):

    def test_demandes_d_inscription_sont_limitees_par_adresse(self):
        cache.clear()
        donnees = {}
        for _ in range(5):
            self.client.post('/pro/inscription/', donnees)
        reponse = self.client.post('/pro/inscription/', donnees)
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'Trop de demandes depuis cette connexion')
