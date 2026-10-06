from django.test import TestCase

from enfants.oms_lms import z_poids_age
from enfants.views import _ligne_muac, evaluer_malnutrition


class LigneMuacTests(TestCase):

    def test_muac_n_est_pas_interprete_avant_six_mois(self):
        evaluation = _ligne_muac(13.0, 4)
        self.assertEqual(evaluation['statut'], 'Non interprétable à cet âge')
        self.assertEqual(evaluation['couleur'], 'info')
        self.assertIn('6 et 59 mois', evaluation['note'])
        self.assertIn('À 4 mois', evaluation['note'])

    def test_muac_n_est_pas_interprete_apres_cinquante_neuf_mois(self):
        evaluation = _ligne_muac(13.0, 60)
        self.assertEqual(evaluation['statut'], 'Non interprétable à cet âge')
        self.assertIn('À 60 mois', evaluation['note'])

    def test_seuils_muac_de_six_a_cinquante_neuf_mois(self):
        cas = (
            (11.4, 'Malnutrition aiguë sévère', 'danger'),
            (12.0, 'Malnutrition aiguë modérée', 'warning'),
            (12.5, 'Normale', 'success'),
        )
        for muac, statut, couleur in cas:
            with self.subTest(muac=muac):
                evaluation = _ligne_muac(muac, 6)
                self.assertEqual(evaluation['statut'], statut)
                self.assertEqual(evaluation['couleur'], couleur)

    def test_sans_muac_aucune_ligne_muac_n_apparait(self):
        evaluations = evaluer_malnutrition(8.0, 70.0, 9, 'M')
        self.assertFalse(any(e['indicateur'] == 'Tour de bras (MUAC)' for e in evaluations))

    def test_oedemes_en_premiere_position_meme_avec_muac_normal(self):
        evaluations = evaluer_malnutrition(14.0, 80.0, 9, 'M', 14.0, oedemes=True)
        self.assertEqual(evaluations[0]['indicateur'], 'Œdèmes bilatéraux')
        self.assertEqual(evaluations[0]['statut'], 'Malnutrition aiguë sévère')
        self.assertEqual(evaluations[0]['couleur'], 'danger')
        self.assertIn('quels que soient le poids et le périmètre brachial', evaluations[0]['note'])

    def test_les_courbes_dependant_du_sexe(self):
        self.assertNotEqual(z_poids_age(8.0, 'M', 9), z_poids_age(8.0, 'F', 9))


class MalnutritionPageTests(TestCase):

    def test_formulaire_precise_la_validite_du_muac_et_les_oedemes(self):
        reponse = self.client.get('/depistage/')
        self.assertContains(reponse, 'Mesure valable de 6 à 59 mois uniquement.')
        self.assertContains(reponse, 'name="oedemes" value="oui"')
        self.assertContains(reponse, 'Appuyez trois secondes')

    def test_resultat_affiche_la_note_du_muac(self):
        reponse = self.client.post('/depistage/', {
            'prenom': 'Awa', 'sexe': 'M', 'age_mois': '4',
            'poids': '6.0', 'taille': '60', 'muac': '13',
        })
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'Non interprétable à cet âge')
        self.assertContains(reponse, 'À 4 mois, la mesure ne permet aucune conclusion')

    def test_oedemes_sont_transmis_a_l_evaluation(self):
        reponse = self.client.post('/depistage/', {
            'prenom': 'Awa', 'sexe': 'M', 'age_mois': '9',
            'poids': '14.0', 'taille': '80', 'muac': '14',
            'oedemes': 'oui',
        })
        evaluation = reponse.context['resultats']['evaluations'][0]
        self.assertEqual(evaluation['indicateur'], 'Œdèmes bilatéraux')
        self.assertIn("Conduisez l'enfant au centre de santé aujourd'hui.", evaluation['note'])


class AdditionalMalnutritionTests(TestCase):

    def test_muac_est_interpretable_a_la_borne_superieure(self):
        evaluation = _ligne_muac(13.0, 59)
        self.assertEqual(evaluation['statut'], 'Normale')
        self.assertNotIn('note', evaluation)

    def test_muac_est_interpretable_a_la_borne_inferieure(self):
        evaluation = _ligne_muac(13.0, 6)
        self.assertEqual(evaluation['couleur'], 'success')

    def test_muac_hors_age_reste_info_meme_s_il_est_bas(self):
        evaluation = _ligne_muac(10.0, 5)
        self.assertEqual(evaluation['couleur'], 'info')
        self.assertEqual(evaluation['statut'], 'Non interprétable à cet âge')

    def test_sans_oedemes_aucune_ligne_oedemes_n_est_ajoutee(self):
        evaluations = evaluer_malnutrition(8.0, 70.0, 9, 'F', 13.0, oedemes=False)
        self.assertFalse(any(e['indicateur'] == 'Œdèmes bilatéraux' for e in evaluations))

    def test_note_des_oedemes_indique_la_conduite_a_tenir(self):
        evaluation = evaluer_malnutrition(5.0, 60.0, 4, 'F', 10.0, oedemes=True)[0]
        self.assertEqual(
            evaluation['note'],
            "Des œdèmes des deux pieds signent une malnutrition aiguë sévère, "
            "quels que soient le poids et le périmètre brachial. Conduisez "
            "l'enfant au centre de santé aujourd'hui.",
        )

    def test_post_sans_muac_ne_contient_pas_de_ligne_muac(self):
        reponse = self.client.post('/depistage/', {
            'prenom': 'Awa', 'sexe': 'F', 'age_mois': '9',
            'poids': '8.0', 'taille': '70',
        })
        self.assertEqual(reponse.status_code, 200)
        self.assertFalse(any(
            e['indicateur'] == 'Tour de bras (MUAC)'
            for e in reponse.context['resultats']['evaluations']
        ))
