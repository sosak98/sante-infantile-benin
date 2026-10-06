"""Tests des jours de vaccination par centre (modèle, page publique, carte)."""

from datetime import date

from django.test import TestCase
from django.utils import timezone

from sante.models import CODES_JOURS, Etablissement, code_du_jour


def creer_centre(**kwargs):
    valeurs = {
        'nom': 'Centre de santé de Gbégamey',
        'type_etab': 'centre',
        'adresse': 'Cotonou, Bénin',
        'commune': 'Cotonou',
        'latitude': 6.37,
        'longitude': 2.41,
        'fait_vaccination': True,
    }
    valeurs.update(kwargs)
    return Etablissement.objects.create(**valeurs)


class JoursVaccinationModeleTests(TestCase):

    def test_jours_liste_nettoyee_et_ordonnee(self):
        centre = creer_centre(jours_vaccination=' MERCREDI , lundi ,lundi')
        self.assertEqual(centre.jours_liste, ['lundi', 'mercredi'])

    def test_jours_liste_ignore_les_valeurs_invalides(self):
        centre = creer_centre(jours_vaccination='lundi,jour-du-poisson')
        self.assertEqual(centre.jours_liste, ['lundi'])

    def test_jours_affichage_lisible(self):
        centre = creer_centre(jours_vaccination='lundi,mardi,vendredi')
        self.assertEqual(centre.jours_affichage, 'Lundi, Mardi et Vendredi')

    def test_jours_affichage_un_seul_jour(self):
        centre = creer_centre(jours_vaccination='jeudi')
        self.assertEqual(centre.jours_affichage, 'Jeudi')

    def test_jours_non_renseignes_sont_annonces_comme_tels(self):
        """On n'invente jamais un horaire : on dit qu'on ne sait pas."""
        centre = creer_centre(jours_vaccination='')
        self.assertFalse(centre.jours_renseignes)
        self.assertEqual(centre.jours_affichage, 'Jours non communiqués')

    def test_vaccine_le_jour_declare(self):
        centre = creer_centre(jours_vaccination='lundi,mercredi')
        self.assertTrue(centre.vaccine_le(date(2026, 1, 5)))    # un lundi
        self.assertFalse(centre.vaccine_le(date(2026, 1, 6)))   # un mardi

    def test_vaccine_le_renvoie_none_si_inconnu(self):
        """None = « on ne sait pas », à distinguer de False = « pas de séance »."""
        self.assertIsNone(creer_centre(jours_vaccination='').vaccine_le(date(2026, 1, 5)))
        self.assertIsNone(
            creer_centre(fait_vaccination=False,
                         jours_vaccination='lundi').vaccine_le(date(2026, 1, 5))
        )

    def test_code_du_jour_suit_le_calendrier(self):
        self.assertEqual(code_du_jour(date(2026, 1, 5)), 'lundi')
        self.assertEqual(code_du_jour(date(2026, 1, 11)), 'dimanche')
        self.assertEqual(len(CODES_JOURS), 7)


class PageJoursVaccinationTests(TestCase):

    def setUp(self):
        self.aujourdhui = code_du_jour()
        self.autre = CODES_JOURS[(CODES_JOURS.index(self.aujourdhui) + 1) % 7]
        self.ouvert = creer_centre(
            nom='CS Ouvert Aujourdhui', jours_vaccination=self.aujourdhui,
            horaire_vaccination='08h00 - 12h00', commune='Cotonou',
            source_vaccination='centre', maj_vaccination=timezone.now(),
        )
        self.ferme = creer_centre(
            nom='CS Autre Jour', jours_vaccination=self.autre, commune='Parakou',
        )
        self.inconnu = creer_centre(nom='CS Sans Jours', jours_vaccination='')
        self.pharmacie = creer_centre(
            nom='Pharmacie du Port', type_etab='pharmacie',
            fait_vaccination=False, jours_vaccination='',
        )

    def test_page_repond_200(self):
        self.assertEqual(self.client.get('/carte/vaccination/').status_code, 200)

    def test_filtre_par_defaut_sur_aujourd_hui(self):
        reponse = self.client.get('/carte/vaccination/')
        self.assertEqual(reponse.context['jour'], self.aujourdhui)
        self.assertContains(reponse, 'CS Ouvert Aujourdhui')
        self.assertNotContains(reponse, 'CS Autre Jour')

    def test_filtre_sur_un_jour_precis(self):
        reponse = self.client.get('/carte/vaccination/', {'jour': self.autre})
        self.assertContains(reponse, 'CS Autre Jour')
        self.assertNotContains(reponse, 'CS Ouvert Aujourdhui')

    def test_filtre_toute_la_semaine(self):
        reponse = self.client.get('/carte/vaccination/', {'jour': 'tous'})
        self.assertContains(reponse, 'CS Ouvert Aujourdhui')
        self.assertContains(reponse, 'CS Autre Jour')

    def test_jour_invalide_retombe_sur_aujourd_hui(self):
        reponse = self.client.get('/carte/vaccination/', {'jour': 'pizza'})
        self.assertEqual(reponse.context['jour'], self.aujourdhui)

    def test_recherche_par_commune(self):
        reponse = self.client.get('/carte/vaccination/',
                                  {'jour': 'tous', 'q': 'Parakou'})
        self.assertContains(reponse, 'CS Autre Jour')
        self.assertNotContains(reponse, 'CS Ouvert Aujourdhui')

    def test_centres_sans_jours_listes_a_part(self):
        """Ils ne sont ni cachés ni présentés comme ouverts."""
        reponse = self.client.get('/carte/vaccination/', {'jour': 'tous'})
        self.assertContains(reponse, 'CS Sans Jours')
        self.assertContains(reponse, 'sans jours communiqués')

    def test_zero_centre_le_jour_choisi_formule_correctement(self):
        """« 0 centres vaccinent le mardi » est du mauvais français."""
        jour_vide = next(j for j in CODES_JOURS
                         if j not in (self.aujourdhui, self.autre))
        reponse = self.client.get('/carte/vaccination/', {'jour': jour_vide})
        self.assertEqual(reponse.context['nb_publies'], 0)
        self.assertContains(reponse, 'Aucun centre ne vaccine le')
        self.assertNotContains(reponse, '0 centre')

    def test_message_vide_sans_espace_avant_le_point(self):
        """« de séance . » : le libellé du jour est absent en vue semaine."""
        Etablissement.objects.all().update(jours_vaccination='')
        reponse = self.client.get('/carte/vaccination/', {'jour': 'tous'})
        self.assertContains(reponse, "publié de séance.")
        self.assertNotContains(reponse, "de séance .")

    def test_pharmacies_exclues(self):
        reponse = self.client.get('/carte/vaccination/', {'jour': 'tous'})
        self.assertNotContains(reponse, 'Pharmacie du Port')

    def test_horaire_affiche(self):
        reponse = self.client.get('/carte/vaccination/')
        self.assertContains(reponse, '08h00 - 12h00')

    def test_lien_vers_espace_professionnels(self):
        reponse = self.client.get('/carte/vaccination/')
        self.assertContains(reponse, '/pro/')


class CarteAvecVaccinationTests(TestCase):

    def test_carte_expose_les_jours_de_vaccination(self):
        creer_centre(nom='CS Cartographie', jours_vaccination='mardi,jeudi')
        reponse = self.client.get('/carte/')
        self.assertEqual(reponse.status_code, 200)
        etab = reponse.context['etablissements'][0]
        self.assertTrue(etab['vaccination'])
        self.assertEqual(etab['jours'], ['mardi', 'jeudi'])

    def test_carte_propose_le_filtre_du_jour(self):
        reponse = self.client.get('/carte/')
        self.assertContains(reponse, 'filtreVaccination')
        self.assertContains(reponse, 'jour-actuel-data')

    def test_carte_echappe_les_noms(self):
        """Les noms viennent d'OpenStreetMap : pas d'injection HTML possible."""
        creer_centre(nom='<script>alert(1)</script>')
        reponse = self.client.get('/carte/')
        self.assertNotContains(reponse, '<script>alert(1)</script>')
        self.assertContains(reponse, 'function echapper')

    def test_carte_utilise_osm_sans_fournisseur_a_cle(self):
        html = self.client.get('/carte/').content.decode('utf-8').lower()
        self.assertNotIn('basemaps.cartocdn.com', html)
        self.assertNotIn('apikey', html)

    def test_carte_annonce_une_erreur_de_tuiles(self):
        self.assertContains(
            self.client.get('/carte/'),
            'La carte ne peut pas se charger. Vérifiez votre connexion.',
        )


class PremiersSecoursTests(TestCase):

    def test_regle_des_cinq_minutes_avant_la_liste_a_faire(self):
        html = self.client.get('/premiers-secours/').content.decode('utf-8')
        debut = html.index('Comptez la durée de la crise')
        a_faire = html.index('À faire', debut)
        self.assertLess(debut, a_faire)
        self.assertIn('Plus de 5 minutes', html)
        self.assertIn('appelez le 112 tout de suite', html)
        self.assertIn('Moins de 5 minutes', html)


class AdditionalPremiersSecoursTests(TestCase):

    def test_encadre_convulsions_est_rouge(self):
        html = self.client.get('/premiers-secours/').content.decode('utf-8')
        debut = html.index('Comptez la durée de la crise')
        encadre = html[html.rfind('<div', 0, debut):debut]
        self.assertIn('alert-danger', encadre)
