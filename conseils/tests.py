"""Tests du calendrier vaccinal PEV Bénin (conseils/pev.py) et de ses pages."""

from datetime import date, timedelta

from django.test import TestCase

from conseils.pev import (
    CALENDRIER_PEV,
    CHIMIOPREVENTION_PALUDISME,
    SUPPLEMENTATIONS,
    adapter_au_centre_detaille,
    ajouter_mois,
    calendrier_affichable,
    normaliser_cle,
    planifier,
    prochain_rdv,
    resume_couverture,
)
from conseils.seed_data import VACCINS
from sante.models import Etablissement


# Programme relevé auprès de CS Dowa : un vaccin par jour.
DOWA = {
    'lundi': {'mode': 'seulement', 'series': ['bcg', 'vpo', 'vpo_naissance']},
    'mardi': {'mode': 'seulement', 'series': ['penta', 'pcv', 'rota', 'vpi']},
    'mercredi': {'mode': 'seulement', 'series': ['vitamine_a']},
    'jeudi': {'mode': 'seulement', 'series': ['penta', 'pcv', 'rota', 'vpi']},
    'vendredi': {'mode': 'seulement', 'series': ['9mois', 'var']},
}


def creer_centre(**kwargs):
    valeurs = {
        'nom': 'CS Dowa', 'type_etab': 'centre', 'adresse': 'Bénin',
        'latitude': 0.0, 'longitude': 0.0, 'fait_vaccination': True,
        'jours_confirmes': True,
        'jours_vaccination': 'lundi,mardi,mercredi,jeudi,vendredi',
        'programme_vaccination': DOWA, 'vaccins_non_proposes': 'rtss',
    }
    valeurs.update(kwargs)
    return Etablissement.objects.create(**valeurs)

NAISSANCE = date(2025, 1, 15)


def _par_cle(planning):
    return {ligne['cle']: ligne for ligne in planning}


class CalendrierReferenceTests(TestCase):
    """Le calendrier doit refléter le PEV béninois en vigueur."""

    def test_les_cles_sont_uniques(self):
        cles = [entree['cle'] for entree in CALENDRIER_PEV]
        self.assertEqual(len(cles), len(set(cles)))

    def test_chaque_entree_a_un_age_unique_semaines_ou_mois(self):
        for entree in CALENDRIER_PEV:
            with self.subTest(cle=entree['cle']):
                self.assertNotEqual(
                    'semaines' in entree, 'mois' in entree,
                    "Une dose doit avoir soit un âge en semaines, soit en mois.",
                )

    def test_doses_de_naissance(self):
        naissance = [e['cle'] for e in CALENDRIER_PEV if e.get('semaines') == 0]
        self.assertCountEqual(naissance, ['bcg', 'vpo_0', 'hepb_0'])

    def test_series_6_10_14_semaines(self):
        """Pentavalent, VPO, PCV et rotavirus suivent bien 6/10/14 semaines."""
        attendus = {'penta': [6, 10, 14], 'vpo': [6, 10],
                    'pcv': [6, 10, 14], 'rota': [6, 10, 14]}
        for serie, semaines in attendus.items():
            obtenues = [e['semaines'] for e in CALENDRIER_PEV if e['serie'] == serie]
            with self.subTest(serie=serie):
                self.assertEqual(obtenues, semaines)

    def test_vpi_present_a_14_semaines(self):
        """Le VPI remplace la troisième dose orale à 14 semaines."""
        vpi = [e for e in CALENDRIER_PEV if e['cle'] == 'vpi']
        self.assertEqual(len(vpi), 1)
        self.assertEqual(vpi[0]['semaines'], 14)
        self.assertIn(
            "Il remplace la troisième dose orale : la série orale s'arrête au VPO 2.",
            vpi[0]['description'],
        )

    def test_vpo_3_est_absent_et_les_anciens_libelles_sont_rattaches_au_vpi(self):
        self.assertFalse(any(e['cle'] == 'vpo_3' for e in CALENDRIER_PEV))
        self.assertTrue(any(e['cle'] == 'vpi' for e in CALENDRIER_PEV))
        self.assertEqual(normaliser_cle('VPO 3'), 'vpi')
        self.assertEqual(normaliser_cle('vpo_3'), 'vpi')

    def test_rotavirus_present_trois_doses(self):
        """Le rotavirus (introduit au Bénin en 2019) manquait au calendrier."""
        rota = [e for e in CALENDRIER_PEV if e['serie'] == 'rota']
        self.assertEqual(len(rota), 3)

    def test_antipaludique_aux_ages_beninois(self):
        """RTS,S : 6, 7, 9 et 18 mois — et non 22/26/39/65 semaines."""
        rtss = [e for e in CALENDRIER_PEV if e['serie'] == 'rtss']
        self.assertEqual([e['mois'] for e in rtss], [6, 7, 9, 18])

    def test_neuf_mois_exprime_en_mois_pas_en_semaines(self):
        """VAR/VAA/MenA étaient calés sur 39 semaines, soit un jour trop tôt."""
        for cle in ('var_1', 'vaa', 'mena'):
            entree = next(e for e in CALENDRIER_PEV if e['cle'] == cle)
            with self.subTest(cle=cle):
                self.assertEqual(entree.get('mois'), 9)
                self.assertNotIn('semaines', entree)

    def test_seconde_dose_rougeole_a_18_mois(self):
        var2 = next(e for e in CALENDRIER_PEV if e['cle'] == 'var_2')
        self.assertEqual(var2['mois'], 18)

    def test_seed_derive_du_calendrier(self):
        """Le seed ne doit plus diverger du calendrier de référence."""
        self.assertEqual(len(VACCINS), len(CALENDRIER_PEV))
        self.assertEqual(
            [v['nom'] for v in VACCINS],
            [e['nom'] for e in CALENDRIER_PEV],
        )

    def test_calendrier_affichable_complet(self):
        lignes = calendrier_affichable()
        self.assertEqual(len(lignes), len(CALENDRIER_PEV))
        for ligne in lignes:
            with self.subTest(cle=ligne['cle']):
                self.assertTrue(ligne['maladies'])
                self.assertTrue(ligne['voie'])

    def test_tpi_est_distinct_du_calendrier_vaccinal(self):
        cles_tpi = [prise['cle'] for prise in CHIMIOPREVENTION_PALUDISME]
        self.assertEqual(cles_tpi, ['tpi_1', 'tpi_2', 'tpi_3'])
        self.assertEqual(
            [prise.get('semaines') for prise in CHIMIOPREVENTION_PALUDISME[:2]],
            [10, 14],
        )
        self.assertEqual(CHIMIOPREVENTION_PALUDISME[2].get('mois'), 9)
        self.assertFalse(set(cles_tpi) & {entree['cle'] for entree in CALENDRIER_PEV})

    def test_vitamine_a_est_une_supplementation_hors_calendrier(self):
        self.assertTrue(any(s['nom'] == 'Vitamine A' for s in SUPPLEMENTATIONS))
        self.assertFalse(any(entree['nom'] == 'Vitamine A' for entree in CALENDRIER_PEV))


class AjouterMoisTests(TestCase):
    """Arithmétique de dates : les mois ne valent pas 4 semaines."""

    def test_ajout_simple(self):
        self.assertEqual(ajouter_mois(date(2025, 1, 15), 9), date(2025, 10, 15))

    def test_fin_de_mois_ramenee_au_dernier_jour(self):
        self.assertEqual(ajouter_mois(date(2025, 1, 31), 1), date(2025, 2, 28))

    def test_annee_bissextile(self):
        self.assertEqual(ajouter_mois(date(2024, 1, 31), 1), date(2024, 2, 29))

    def test_changement_d_annee(self):
        self.assertEqual(ajouter_mois(date(2025, 11, 10), 3), date(2026, 2, 10))

    def test_neuf_mois_differe_de_39_semaines(self):
        """La correction de fond : 39 semaines n'est pas 9 mois.

        L'ancien calendrier plaçait VAR/VAA/MenA à 39 semaines. Pour un enfant
        né le 31 mars, cela avance le rendez-vous de deux jours.
        """
        naissance = date(2025, 3, 31)
        self.assertEqual(ajouter_mois(naissance, 9), date(2025, 12, 31))
        self.assertEqual(naissance + timedelta(weeks=39), date(2025, 12, 29))


class NormalisationTests(TestCase):
    """Les anciens libellés doivent être reconnus, sinon les doses sont perdues."""

    def test_anciennes_cles_reconnues(self):
        cas = {
            'Pentavalent_1': 'penta_1',
            'VPO_2': 'vpo_2',
            'PCV_3': 'pcv_3',
            'RTSS_4': 'rtss_4',
            'VAR': 'var_1',
            'Hépatite B': 'hepb_0',
            'Hepatite B': 'hepb_0',
            'VPO 0 (Polio oral)': 'vpo_0',
            'Vaccin Antipaludique 1 (RTS,S)': 'rtss_1',
        }
        for ancien, attendu in cas.items():
            with self.subTest(ancien=ancien):
                self.assertEqual(normaliser_cle(ancien), attendu)

    def test_cles_nouvelles_inchangees(self):
        for entree in CALENDRIER_PEV:
            with self.subTest(cle=entree['cle']):
                self.assertEqual(normaliser_cle(entree['cle']), entree['cle'])

    def test_libelle_inconnu_renvoie_none(self):
        """Mieux vaut ignorer une saisie inconnue que l'affecter au mauvais vaccin."""
        self.assertIsNone(normaliser_cle('Vaccin fantaisiste'))
        self.assertIsNone(normaliser_cle(''))
        self.assertIsNone(normaliser_cle(None))

    def test_casse_et_espaces_ignores(self):
        self.assertEqual(normaliser_cle('  bcg  '), 'bcg')
        self.assertEqual(normaliser_cle('BCG'), 'bcg')


class PlanificationTests(TestCase):

    def test_planning_couvre_toutes_les_doses(self):
        planning = planifier(NAISSANCE, {}, date(2025, 1, 15))
        self.assertEqual(len(planning), len(CALENDRIER_PEV))

    def test_planning_trie_par_date(self):
        planning = planifier(NAISSANCE, {}, date(2025, 6, 1))
        dates = [ligne['date_prevue'] for ligne in planning]
        self.assertEqual(dates, sorted(dates))

    def test_dates_theoriques_exactes(self):
        planning = _par_cle(planifier(NAISSANCE, {}, NAISSANCE))
        self.assertEqual(planning['bcg']['date_prevue'], date(2025, 1, 15))
        self.assertEqual(planning['penta_1']['date_prevue'], date(2025, 2, 26))
        self.assertEqual(planning['penta_3']['date_prevue'], date(2025, 4, 23))
        self.assertEqual(planning['var_1']['date_prevue'], date(2025, 10, 15))
        self.assertEqual(planning['rtss_4']['date_prevue'], date(2026, 7, 15))

    def test_statuts_selon_la_date_du_jour(self):
        planning = _par_cle(planifier(NAISSANCE, {}, date(2025, 2, 26)))
        self.assertEqual(planning['bcg']['statut'], 'En retard')
        self.assertEqual(planning['penta_1']['statut'], "Aujourd'hui")
        self.assertEqual(planning['penta_2']['statut'], 'À venir')

    def test_dose_recue_est_marquee(self):
        planning = _par_cle(planifier(
            NAISSANCE, {'bcg': date(2025, 1, 16)}, date(2025, 3, 1),
        ))
        self.assertEqual(planning['bcg']['statut'], 'Reçu')
        self.assertEqual(planning['bcg']['date_prevue'], date(2025, 1, 16))

    def test_dose_recue_sous_ancien_libelle(self):
        """Le bug de fond : « Pentavalent_1 » n'était jamais reconnu."""
        planning = _par_cle(planifier(
            NAISSANCE, {'Pentavalent_1': date(2025, 3, 1)}, date(2025, 4, 1),
        ))
        self.assertEqual(planning['penta_1']['statut'], 'Reçu')

    def test_intervalle_minimal_repousse_la_dose_suivante(self):
        """Penta 1 reçu en retard décale Penta 2 d'au moins 4 semaines."""
        planning = _par_cle(planifier(
            NAISSANCE, {'penta_1': date(2025, 5, 1)}, date(2025, 5, 2),
        ))
        self.assertGreaterEqual(
            planning['penta_2']['date_prevue'], date(2025, 5, 29),
        )

    def test_retard_calcule_en_jours(self):
        planning = _par_cle(planifier(NAISSANCE, {}, date(2025, 1, 25)))
        self.assertEqual(planning['bcg']['retard_jours'], 10)

    def test_date_future_sans_retard(self):
        planning = _par_cle(planifier(NAISSANCE, {}, NAISSANCE))
        self.assertEqual(planning['var_1']['retard_jours'], 0)

    def test_prochain_rdv_priorise_le_retard(self):
        suivant = prochain_rdv(NAISSANCE, {}, date(2025, 3, 1))
        self.assertEqual(suivant['statut'], 'En retard')

    def test_prochain_rdv_sans_retard(self):
        suivant = prochain_rdv(NAISSANCE, {}, NAISSANCE)
        self.assertEqual(suivant['statut'], "Aujourd'hui")

    def test_prochain_rdv_none_si_tout_recu(self):
        tout = {e['cle']: NAISSANCE for e in CALENDRIER_PEV}
        self.assertIsNone(prochain_rdv(NAISSANCE, tout, date(2027, 1, 1)))

    def test_resume_couverture(self):
        resume = resume_couverture(NAISSANCE, {'bcg': NAISSANCE}, date(2025, 1, 15))
        self.assertEqual(resume['total'], len(CALENDRIER_PEV))
        self.assertEqual(resume['recus'], 1)
        self.assertEqual(
            resume['recus'] + resume['en_retard'] + resume['aujourd_hui']
            + resume['a_venir'] + resume['maternite'],
            resume['total'],
        )


class PagesVaccinationTests(TestCase):
    """Les pages publiques du module vaccination."""

    def test_calendrier_affiche_sans_seed(self):
        """La page était vide si `manage.py seed` n'avait pas tourné."""
        reponse = self.client.get('/conseils/')
        self.assertEqual(reponse.status_code, 200)
        html = reponse.content.decode('utf-8')
        self.assertNotIn('Aucun vaccin enregistré', html)
        for attendu in ['BCG', 'Pentavalent 1', 'Rotavirus 1',
                        'VPI (polio injectable)', 'Antipaludique 1 (RTS,S)',
                        'VAR 2 (rappel rougeole-rubéole)']:
            with self.subTest(attendu=attendu):
                self.assertIn(attendu, html)

    def test_calendrier_mentionne_les_supplementations(self):
        reponse = self.client.get('/conseils/')
        self.assertContains(reponse, 'Vitamine A')
        self.assertContains(reponse, 'Chimioprévention du paludisme (TPI)')
        self.assertContains(reponse, 'trois prises orales de sulfadoxine-pyriméthamine')
        self.assertNotContains(reponse, 'TPI 1 (sulfadoxine-pyriméthamine)')

    def test_calendrier_sans_colonne_voie(self):
        """La voie d'administration est une information de soignant, pas de
        parent : elle reste en base mais quitte l'affichage public."""
        html = self.client.get('/conseils/').content.decode('utf-8')
        self.assertNotIn('<th>Voie</th>', html)

    def test_rdv_calcule_un_planning(self):
        reponse = self.client.post('/conseils/rdv/', {
            'date_naissance': '2025-01-15',
        })
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'BCG')
        self.assertNotContains(reponse, 'TPI 1 (sulfadoxine-pyriméthamine)')
        self.assertNotContains(reponse, 'Vitamine A')

    def test_hepatite_b_a_la_maternite_est_affichee_comme_ok(self):
        reponse = self.client.post('/conseils/rdv/', {
            'date_naissance': '2025-01-15',
        })
        self.assertContains(
            reponse,
            'id="rdv-hepb_0" data-cle="hepb_0" class="tl-item ok"',
        )
        self.assertContains(
            reponse,
            "Administré en salle d'accouchement dans les 24 heures suivant la naissance.",
        )

    def test_rdv_sans_centre_affiche_le_repli(self):
        reponse = self.client.get('/conseils/rdv/')
        self.assertContains(
            reponse,
            "Ces dates suivent le calendrier national du PEV. Les jours de séance varient d'un centre à l'autre : sélectionnez votre centre ci-dessus pour obtenir les dates réelles de ses séances. Si votre centre n'apparaît pas dans la liste, c'est qu'il n'a pas encore déclaré ses jours de vaccination.",
        )

    def test_rdv_refuse_une_date_invalide_sans_erreur_500(self):
        """Une saisie invalide renvoyait une erreur 500."""
        reponse = self.client.post('/conseils/rdv/', {'date_naissance': 'n-importe-quoi'})
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'date de naissance valide')

    def test_rdv_refuse_une_naissance_future(self):
        futur = (date.today() + timedelta(days=30)).isoformat()
        reponse = self.client.post('/conseils/rdv/', {'date_naissance': futur})
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'ne peut pas être dans le futur')


class AdditionalPolioTests(TestCase):

    def test_vpo_et_vpi_sont_deux_series_distinctes(self):
        self.assertEqual(
            [e['cle'] for e in CALENDRIER_PEV if e['serie'] == 'vpo'],
            ['vpo_1', 'vpo_2'],
        )
        self.assertEqual(
            [e['cle'] for e in CALENDRIER_PEV if e['serie'] == 'vpi'],
            ['vpi'],
        )

    def test_description_du_vpi_est_complete(self):
        vpi = next(e for e in CALENDRIER_PEV if e['cle'] == 'vpi')
        self.assertEqual(
            vpi['description'],
            "Vaccin polio inactivé injectable, administré à 14 semaines. "
            "Il remplace la troisième dose orale : la série orale s'arrête au VPO 2.",
        )

    def test_calendrier_affichable_ne_propose_pas_de_vpo_3(self):
        self.assertNotIn('VPO 3', {ligne['nom'] for ligne in calendrier_affichable()})

    def test_ancien_libelle_vpo_3_est_reconnu_avec_espaces(self):
        self.assertEqual(normaliser_cle('  VPO 3  '), 'vpi')


class AdapterAuCentreDetailleTests(TestCase):
    """Le calculateur demande au centre, dose par dose, ses jours de séance."""

    def setUp(self):
        self.dowa = creer_centre()

    def _planning(self, naissance=NAISSANCE, recus=None, aujourd_hui=None):
        planning = planifier(naissance, recus or {}, aujourd_hui or naissance)
        return {ligne['cle']: ligne
                for ligne in adapter_au_centre_detaille(planning, self.dowa)}

    def test_le_bcg_tombe_le_jour_du_bcg(self):
        """CS Dowa vaccine le BCG le lundi, et seulement le lundi."""
        self.assertEqual(self._planning()['bcg']['date_centre'].weekday(), 0)

    def test_le_pentavalent_tombe_un_jour_pentavalent(self):
        planning = self._planning()
        for cle in ('penta_1', 'penta_2', 'penta_3'):
            with self.subTest(cle=cle):
                self.assertIn(planning[cle]['date_centre'].weekday(), (1, 3))

    def test_pcv_13_et_rotavirus_suivent_le_pentavalent(self):
        """Les vaccins de 6, 10 et 14 semaines s'administrent ensemble."""
        planning = self._planning()
        self.assertEqual(planning['pcv_1']['date_centre'], planning['penta_1']['date_centre'])
        self.assertEqual(planning['rota_1']['date_centre'], planning['penta_1']['date_centre'])
        self.assertEqual(planning['vpi']['date_centre'], planning['penta_3']['date_centre'])

    def test_les_doses_de_neuf_mois_tombent_un_vendredi(self):
        """Var, VAA et MenA : le 15 octobre 2025 tombe un mercredi, donc vendredi 17."""
        planning = self._planning()
        self.assertEqual(planning['var_1']['date_centre'], date(2025, 10, 17))
        for cle in ('var_1', 'vaa', 'mena'):
            with self.subTest(cle=cle):
                self.assertEqual(planning[cle]['date_centre'].weekday(), 4)

    def test_aucune_dose_n_est_programmee_avant_sa_date_theorique(self):
        for ligne in self._planning(naissance=date(2025, 1, 17)).values():
            if ligne['non_administre_ici']:
                continue
            with self.subTest(cle=ligne['cle']):
                self.assertGreaterEqual(ligne['date_centre'], ligne['date_prevue'])

    def test_l_intervalle_de_28_jours_survit_au_report(self):
        """Une dose reportée décale la suivante d'au moins 28 jours."""
        planning = self._planning(naissance=date(2025, 1, 17))   # un vendredi
        for premiere, suivante in (('penta_1', 'penta_2'), ('penta_2', 'penta_3'),
                                   ('vpo_1', 'vpo_2')):
            with self.subTest(serie=(premiere, suivante)):
                ecart = planning[suivante]['date_centre'] - planning[premiere]['date_centre']
                self.assertGreaterEqual(ecart.days, 28)

    def test_chaque_dose_repart_de_la_date_retenue_pour_la_precedente(self):
        """On ne rapproche jamais deux doses : la précédente compte, pas le calendrier."""
        centre = creer_centre(
            nom='CS Doses Var', vaccins_non_proposes='',
            jours_vaccination='lundi,vendredi',
            programme_vaccination={
                'lundi': {'mode': 'seulement', 'series': ['var']},
                'vendredi': {'mode': 'seulement', 'series': ['9mois']},
            },
        )
        planning = [
            {'cle': 'var_1', 'nom': 'VAR 1', 'serie': 'var', 'dose': 1,
             'date_prevue': date(2025, 3, 7), 'statut': 'À venir', 'age_mois': 9,
             'maternite': False, 'couleur': 'info', 'retard_jours': 0},
            {'cle': 'var_2', 'nom': 'VAR 2', 'serie': 'var', 'dose': 2,
             'date_prevue': date(2025, 3, 14), 'statut': 'À venir', 'age_mois': 18,
             'maternite': False, 'couleur': 'info', 'retard_jours': 0},
        ]
        resultat = {ligne['cle']: ligne for ligne in adapter_au_centre_detaille(planning, centre)}
        self.assertEqual(resultat['var_1']['date_centre'], date(2025, 3, 7))
        # Le lundi 10 mars serait trop tôt : 3 jours après la deuxième dose.
        self.assertGreaterEqual(
            (resultat['var_2']['date_centre'] - resultat['var_1']['date_centre']).days, 28,
        )
        self.assertEqual(resultat['var_2']['date_centre'], date(2025, 4, 7))

    def test_un_vaccin_non_propose_n_a_pas_de_date(self):
        planning = self._planning()
        for cle in ('rtss_1', 'rtss_2', 'rtss_3', 'rtss_4'):
            with self.subTest(cle=cle):
                self.assertIsNone(planning[cle]['date_centre'])
                self.assertTrue(planning[cle]['non_administre_ici'])
                self.assertNotEqual(planning[cle]['statut'], 'En retard')
        # Les autres doses restent programmées.
        self.assertIsNotNone(planning['var_1']['date_centre'])
        self.assertFalse(planning['var_1']['non_administre_ici'])

    def test_les_doses_trop_vieilles_ne_sont_pas_signalees_en_retard(self):
        """Le 3 juillet 2026, la dose de RTS,S du 15 juillet 2026 est à venir."""
        planning = self._planning(aujourd_hui=date(2026, 8, 1))
        self.assertIsNone(planning['rtss_1']['date_centre'])
        self.assertTrue(planning['rtss_1']['non_administre_ici'])


class PageRdvAvecCentreTests(TestCase):
    """La page de rendez-vous quand le centre a un programme détaillé."""

    def setUp(self):
        self.dowa = creer_centre()

    def _poster(self, naissance=None):
        return self.client.post('/conseils/rdv/', {
            'date_naissance': (naissance or date.today()).isoformat(),
            'centre_id': self.dowa.pk,
        })

    def _resultats(self, reponse):
        return {ligne['cle']: ligne for ligne in reponse.context['resultats']}

    def test_la_page_annonce_le_programme_du_centre(self):
        reponse = self._poster()
        self.assertContains(reponse, 'Séances de ce centre')
        self.assertContains(reponse, 'Lundi : BCG, VPO')
        self.assertContains(reponse, 'Mardi : Pentavalent, PCV-13')
        self.assertContains(reponse, 'Vendredi : 9 mois, VAR')

    def test_la_page_annonce_les_vaccins_non_proposes(self):
        self.assertContains(self._poster(), 'Non proposé dans ce centre : Antipaludique RTS,S')

    def test_une_dose_non_proposee_est_neutre_et_pas_en_retard(self):
        reponse = self._poster()
        self.assertContains(
            reponse,
            "Ce centre ne propose pas cette dose. Renseignez-vous auprès d'un autre centre, "
            "ou demandez-leur directement.",
        )
        self.assertContains(reponse, 'selon le calendrier national.')
        self.assertContains(reponse, 'id="rdv-rtss_3" data-cle="rtss_3" class="tl-item neutral"')
        self.assertNotContains(reponse, 'En retard')

    def test_les_autres_doses_restent_programmees_sur_les_jours_du_centre(self):
        reponse = self._poster()
        resultats = self._resultats(reponse)
        self.assertIsNone(resultats['rtss_1']['date_centre'])
        self.assertTrue(resultats['rtss_1']['non_administre_ici'])
        self.assertEqual(resultats['penta_1']['date_centre'].weekday(), 1)   # mardi
        self.assertEqual(resultats['bcg']['date_centre'].weekday(), 0)       # lundi
        self.assertIsNotNone(resultats['var_1']['date_centre'])

    def test_le_centre_choisi_est_pris_en_compte(self):
        """Le sélecteur de centre doit être dans le formulaire (sinon rien n'est envoyé)."""
        reponse = self._poster()
        self.assertTrue(reponse.context['centre'])
        self.assertEqual(reponse.context['centre'].pk, self.dowa.pk)

    def test_centre_sans_programme_detaille_utilise_ses_jours_d_ouverture(self):
        centre = creer_centre(
            nom='CS Sans Programme Détaille', programme_vaccination={},
            jours_vaccination='mardi,jeudi',
        )
        reponse = self.client.post('/conseils/rdv/', {
            'date_naissance': date.today().isoformat(), 'centre_id': centre.pk,
        })
        resultats = {ligne['cle']: ligne for ligne in reponse.context['resultats']}
        for cle in ('penta_1', 'pcv_1', 'var_1', 'rtss_1'):
            with self.subTest(cle=cle):
                self.assertIn(resultats[cle]['date_centre'].weekday(), (1, 3))
