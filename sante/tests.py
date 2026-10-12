"""Tests des jours de vaccination par centre (modèle, page publique, carte)."""

from datetime import date
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from conseils.pev import CALENDRIER_PEV, adapter_au_centre_detaille, planifier
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


# Programme relevé auprès de CS Dowa : un vaccin par jour.
PROGRAMME_DOWA = {
    'lundi': {'mode': 'seulement', 'series': ['bcg', 'vpo', 'vpo_naissance']},
    'mardi': {'mode': 'seulement', 'series': ['penta', 'pcv', 'rota', 'vpi']},
    'mercredi': {'mode': 'seulement', 'series': ['vitamine_a']},
    'jeudi': {'mode': 'seulement', 'series': ['penta', 'pcv', 'rota', 'vpi']},
    'vendredi': {'mode': 'seulement', 'series': ['9mois', 'var']},
}


class ProgrammeVaccinationTests(TestCase):
    """Le programme détaillé : les centres organisent leurs séances par vaccin."""

    def setUp(self):
        self.dowa = creer_centre(
            nom='CS Dowa', vaccins_non_proposes='rtss',
            jours_vaccination='lundi,mardi,mercredi,jeudi,vendredi',
            programme_vaccination=PROGRAMME_DOWA,
        )

    def test_le_bcg_tombe_le_jour_du_bcg(self):
        self.assertEqual(self.dowa.jours_pour('bcg'), ['lundi'])

    def test_le_pentavalent_tombe_les_jours_pentavalent(self):
        self.assertEqual(self.dowa.jours_pour('penta'), ['mardi', 'jeudi'])

    def test_pcv_et_rotavirus_suivent_le_pentavalent_le_meme_jour(self):
        """Un jour « Pentavalent » vaut aussi PCV-13, rotavirus et VPI."""
        jour_penta = self.dowa.jours_pour('penta')
        for serie in ('pcv', 'rota', 'vpi'):
            with self.subTest(serie=serie):
                self.assertEqual(self.dowa.jours_pour(serie), jour_penta)

    def test_pcv_suit_le_pentavalent_meme_sans_etre_cite(self):
        centre = creer_centre(
            nom='CS Jour Pentavalent',
            programme_vaccination={'mardi': {'mode': 'seulement', 'series': ['penta']}},
        )
        self.assertEqual(centre.jours_pour('pcv'), ['mardi'])
        self.assertEqual(centre.jours_pour('rota'), ['mardi'])
        self.assertEqual(centre.jours_pour('vpi'), ['mardi'])

    def test_la_vitamine_a_tombe_le_jour_de_la_vitamine_a(self):
        self.assertEqual(self.dowa.jours_pour('vitamine_a'), ['mercredi'])

    def test_les_doses_de_neuf_mois_tombent_le_jour_dedie(self):
        for serie in ('var', 'vaa', 'mena'):
            with self.subTest(serie=serie):
                self.assertEqual(self.dowa.jours_pour(serie, age_mois=9), ['vendredi'])
        # Et le RTS,S, que ce centre ne reçoit pas, n'a aucun jour.
        self.assertEqual(self.dowa.jours_pour('rtss', age_mois=9), [])

    def test_un_jour_tous_sauf_bcg_ne_programme_pas_le_bcg(self):
        nikki = creer_centre(
            nom='CS Nikki',
            jours_vaccination='lundi,mardi,mercredi,jeudi,vendredi',
            programme_vaccination={
                'lundi': {'mode': 'seulement', 'series': ['bcg']},
                'mardi': {'mode': 'tous_sauf', 'series': ['bcg']},
                'mercredi': {'mode': 'tous_sauf', 'series': ['bcg']},
                'jeudi': {'mode': 'tous_sauf', 'series': ['bcg']},
                'vendredi': {'mode': 'tous_sauf', 'series': ['bcg']},
            },
        )
        self.assertEqual(nikki.jours_pour('bcg'), ['lundi'])
        self.assertIn('mardi', nikki.jours_pour('penta'))
        self.assertNotIn('mardi', nikki.jours_pour('bcg'))

    def test_un_jour_tous_sauf_9mois_reserve_les_doses_de_neuf_mois(self):
        akogbato = creer_centre(
            nom='CS Akogbato',
            jours_vaccination='lundi,mardi,mercredi,jeudi,vendredi',
            programme_vaccination={
                'lundi': {'mode': 'tous_sauf', 'series': ['9mois']},
                'mardi': {'mode': 'tous_sauf', 'series': ['9mois']},
                'mercredi': {'mode': 'tous_sauf', 'series': ['9mois']},
                'jeudi': {'mode': 'tous_sauf', 'series': ['9mois']},
                'vendredi': {'mode': 'tous'},
            },
        )
        self.assertEqual(akogbato.jours_pour('var', age_mois=9), ['vendredi'])
        self.assertEqual(akogbato.jours_pour('var', age_mois=18),
                         ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi'])

    def test_sans_programme_detaille_le_centre_fait_tous_ses_jours(self):
        """Un centre qui n'a déclaré que ses jours ouvre pour tout, ces jours-là."""
        centre = creer_centre(nom='CS Sans Programme', jours_vaccination='mardi,jeudi')
        for serie in ('bcg', 'penta', 'var', 'rtss'):
            with self.subTest(serie=serie):
                self.assertEqual(centre.jours_pour(serie, age_mois=9), ['mardi', 'jeudi'])

    def test_un_vaccin_exclu_n_a_aucun_jour_meme_un_jour_tous(self):
        """Le centre ne reçoit pas le RTS,S : aucun jour, et les autres restent."""
        centre = creer_centre(
            nom='CS Sans Antipaludique', vaccins_non_proposes='rtss',
            jours_vaccination='lundi,mardi,mercredi,jeudi,vendredi',
            programme_vaccination={
                'lundi': {'mode': 'tous'},
                'mardi': {'mode': 'tous'},
                'mercredi': {'mode': 'tous'},
                'jeudi': {'mode': 'tous'},
                'vendredi': {'mode': 'tous'},
            },
        )
        self.assertEqual(centre.jours_pour('rtss', age_mois=6), [])
        self.assertEqual(centre.jours_pour('rtss', age_mois=9), [])
        self.assertEqual(centre.jours_pour('bcg'),
                         ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi'])

    def test_non_proposes_liste_et_libelles(self):
        self.assertEqual(self.dowa.non_proposes_liste, ['rtss'])
        self.assertEqual(self.dowa.non_proposes_libelles, ['Antipaludique RTS,S'])
        self.assertEqual(creer_centre(nom='CS Tout').non_proposes_liste, [])

    def test_groupes_couvrent_toutes_les_series_du_calendrier(self):
        for entree in CALENDRIER_PEV:
            with self.subTest(serie=entree['serie']):
                self.assertIn(entree['serie'], Etablissement.GROUPES)
        self.assertIn('vitamine_a', Etablissement.GROUPES)
        self.assertIn('9mois', Etablissement.GROUPES)

    def test_programme_affichage_en_clair(self):
        affichage = self.dowa.programme_affichage
        self.assertIn('Lundi : BCG, VPO', affichage)
        self.assertIn('Mardi : Pentavalent, PCV-13', affichage)
        self.assertIn('Mercredi : Vitamine A', affichage)
        self.assertIn('Vendredi : 9 mois, VAR', affichage)
        self.assertNotIn('samedi', affichage.lower())

    def test_programme_affichage_vide_sans_programme(self):
        self.assertEqual(creer_centre(nom='CS Muet').programme_affichage, '')


class SeedCentresVaccinationTests(TestCase):
    """Les neuf centres réels et le programme relevé sur place."""

    def setUp(self):
        call_command('seed_centres_vaccination', stdout=StringIO())
        self.centres = {c.nom: c for c in Etablissement.objects.all()}

    def test_les_neuf_centres_et_idempotence(self):
        self.assertEqual(len(self.centres), 9)
        call_command('seed_centres_vaccination', stdout=StringIO())
        self.assertEqual(Etablissement.objects.count(), 9)

    def test_programme_declare_par_le_centre(self):
        for nom, centre in self.centres.items():
            with self.subTest(centre=nom):
                self.assertTrue(centre.fait_vaccination)
                self.assertTrue(centre.jours_confirmes)
                self.assertEqual(centre.source_vaccination, 'centre')
                self.assertTrue(centre.programme_vaccination)

    def test_jours_vaccination_deduits_des_cles_du_programme(self):
        for nom, centre in self.centres.items():
            with self.subTest(centre=nom):
                self.assertEqual(set(centre.jours_liste), set(centre.programme_vaccination))

    def test_seul_cs_akogbato_propose_l_antipaludique(self):
        for nom, centre in self.centres.items():
            with self.subTest(centre=nom):
                if nom == 'CS Akogbato':
                    self.assertEqual(centre.non_proposes_liste, [])
                    self.assertNotEqual(centre.jours_pour('rtss', age_mois=6), [])
                else:
                    self.assertEqual(centre.non_proposes_liste, ['rtss'])
                    self.assertEqual(centre.jours_pour('rtss', age_mois=6), [])

    def test_aucune_dose_orpheline_hormis_le_vaccin_non_propose(self):
        for nom, centre in self.centres.items():
            planning = adapter_au_centre_detaille(
                planifier(date(2025, 1, 15), {}, date(2025, 1, 15)), centre,
            )
            for ligne in planning:
                with self.subTest(centre=nom, cle=ligne['cle']):
                    if ligne['non_administre_ici']:
                        self.assertIn(ligne['serie'], centre.non_proposes_liste)
                    else:
                        self.assertIsNotNone(ligne['date_centre'])

    def test_coordonnees_connues_et_aucune_inventee(self):
        akogbato = self.centres['CS Akogbato']
        self.assertEqual(akogbato.latitude, 6.35775)
        self.assertEqual(akogbato.longitude, 2.35839)
        self.assertEqual(akogbato.commune, 'Cotonou')
        bohicon = self.centres['CS Bohicon 2']
        self.assertEqual(bohicon.latitude, 7.17926)
        self.assertEqual(bohicon.longitude, 2.06601)
        self.assertEqual(bohicon.commune, 'Bohicon')
        for nom in ('CS Dowa', 'CS Sori', 'CS Aledjo', 'CSC Materi', 'CS Semere',
                    'CS Nikki', 'CS Kpolokoue'):
            with self.subTest(centre=nom):
                centre = self.centres[nom]
                self.assertEqual((centre.latitude, centre.longitude), (0.0, 0.0))
                self.assertEqual(centre.commune, '')

    def test_jours_de_neuf_mois_de_dowa(self):
        """CS Dowa ne vaccine les doses de 9 mois que le vendredi."""
        self.assertEqual(self.centres['CS Dowa'].jours_pour('9mois', age_mois=9), ['vendredi'])
