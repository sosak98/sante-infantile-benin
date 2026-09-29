"""Tests de l'espace parent : tableau de bord et rappels vaccinaux."""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Parent
from enfants.models import Enfant, VaccinRecu


class TableauDeBordTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='maman@test.bj', password='MotDePasse123', first_name='Awa',
        )
        self.parent = Parent.objects.create(
            user=self.user, telephone='97000000', prenom='Awa', nom='Koffi',
        )
        self.client.login(username='maman@test.bj', password='MotDePasse123')

    def _enfant(self, mois):
        """Un enfant né il y a `mois` mois."""
        naissance = date.today() - timedelta(days=int(mois * 30.44))
        return Enfant.objects.create(
            parent=self.parent, nom='Koffi', prenom='Ami',
            date_naissance=naissance, sexe='F',
        )

    def test_tableau_de_bord_accessible(self):
        reponse = self.client.get('/dashboard/')
        self.assertEqual(reponse.status_code, 200)

    def test_sans_enfant_aucun_rappel(self):
        reponse = self.client.get('/dashboard/')
        self.assertEqual(reponse.context['vaccins_en_retard_count'], 0)
        self.assertEqual(reponse.context['prochains_rdv'], [])

    def test_nouveau_ne_a_des_doses_a_venir(self):
        self._enfant(0)
        reponse = self.client.get('/dashboard/')
        self.assertGreater(reponse.context['vaccins_a_venir_count'], 0)

    def test_enfant_non_vaccine_est_signale_en_retard(self):
        self._enfant(12)
        reponse = self.client.get('/dashboard/')
        self.assertGreater(reponse.context['vaccins_en_retard_count'], 0)
        self.assertContains(reponse, 'en retard')

    def test_prochain_rdv_est_propose(self):
        self._enfant(3)
        reponse = self.client.get('/dashboard/')
        self.assertTrue(reponse.context['prochains_rdv'])
        premier = reponse.context['prochains_rdv'][0]
        self.assertIn('rdv', premier)
        self.assertIn('enfant', premier)

    def test_doses_enregistrees_reduisent_le_retard(self):
        """Une dose enregistrée doit être reconnue par le planificateur."""
        enfant = self._enfant(12)
        avant = self.client.get('/dashboard/').context['vaccins_en_retard_count']
        for cle in ['bcg', 'vpo_0', 'hepb_0', 'penta_1']:
            VaccinRecu.objects.create(
                enfant=enfant, nom_vaccin=cle,
                date_reelle=enfant.date_naissance + timedelta(days=1),
            )
        apres = self.client.get('/dashboard/').context['vaccins_en_retard_count']
        self.assertEqual(apres, avant - 4)

    def test_ancien_libelle_de_dose_est_reconnu(self):
        """Les doses saisies avant l'unification des clés restent comptées."""
        enfant = self._enfant(12)
        avant = self.client.get('/dashboard/').context['vaccins_en_retard_count']
        VaccinRecu.objects.create(
            enfant=enfant, nom_vaccin='Pentavalent_1',
            date_reelle=enfant.date_naissance + timedelta(weeks=6),
        )
        apres = self.client.get('/dashboard/').context['vaccins_en_retard_count']
        self.assertEqual(apres, avant - 1)

    def test_dashboard_renvoie_vers_les_jours_de_vaccination(self):
        self._enfant(12)
        self.assertContains(self.client.get('/dashboard/'), '/carte/vaccination/')
