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
        self.assertEqual(apres, avant - 3)

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


class CreatesuperuserAutoTests(TestCase):
    """Le compte administrateur vient de l'environnement, jamais du code."""

    def _lancer(self, **env):
        import os
        from unittest import mock
        from io import StringIO
        from django.core.management import call_command
        sortie = StringIO()
        variables = {k: v for k, v in env.items()}
        with mock.patch.dict(os.environ, variables, clear=False):
            for cle in ('DJANGO_SUPERUSER_USERNAME', 'DJANGO_SUPERUSER_EMAIL',
                        'DJANGO_SUPERUSER_PASSWORD'):
                if cle not in variables:
                    os.environ.pop(cle, None)
            call_command('createsuperuser_auto', stdout=sortie)
        return sortie.getvalue()

    def test_sans_mot_de_passe_ne_touche_a_rien_et_ne_bloque_pas(self):
        """Variable absente = compte géré à la main : avertissement, aucune
        création, et surtout pas d'échec qui bloquerait le déploiement."""
        sortie = self._lancer()
        self.assertIn('DJANGO_SUPERUSER_PASSWORD absente', sortie)
        self.assertFalse(User.objects.filter(is_superuser=True).exists())

    def test_creation_depuis_l_environnement(self):
        self._lancer(DJANGO_SUPERUSER_USERNAME='admin_test',
                     DJANGO_SUPERUSER_EMAIL='admin@exemple.bj',
                     DJANGO_SUPERUSER_PASSWORD='UnMotDePasseSolide2026!')
        admin = User.objects.get(username='admin_test')
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.check_password('UnMotDePasseSolide2026!'))

    def test_idempotente_et_synchronise_le_mot_de_passe(self):
        self._lancer(DJANGO_SUPERUSER_USERNAME='admin_test',
                     DJANGO_SUPERUSER_PASSWORD='UnMotDePasseSolide2026!')
        self._lancer(DJANGO_SUPERUSER_USERNAME='admin_test',
                     DJANGO_SUPERUSER_PASSWORD='UnAutreMotDePasse2026!')
        self.assertEqual(User.objects.filter(username='admin_test').count(), 1)
        admin = User.objects.get(username='admin_test')
        self.assertTrue(admin.check_password('UnAutreMotDePasse2026!'))
