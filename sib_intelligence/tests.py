"""Tests du triage pédiatrique.

Deux défauts cliniques sont couverts ici :
1. les signes généraux de danger de la PCIME étaient additionnés au score, si
   bien qu'une convulsion isolée (4 points sur un seuil de 6) ressortait en
   consultation sous 48 heures. Ils court-circuitent désormais le score ;
2. un IMC brut était comparé à des seuils fixes de 14 et 16, alors qu'un IMC
   n'a pas de sens avant cinq ans. Il est remplacé par le poids pour la taille
   en écarts-types, selon les standards OMS.

Sources :
- PCIME Bénin, OMS, signes généraux de danger :
  https://platform.who.int/docs/default-source/mca-documents/policy-documents/operational-guidance/ben-mn-62-01-operationalguidance-fra-imnci-booklet.pdf
- OMS et UNICEF, 2009, seuil du périmètre brachial porté à 115 mm de 6 à
  59 mois : https://www.who.int/publications/i/item/9789241598163
- OMS, malnutrition aiguë sévère avant 6 mois, poids pour la taille sous moins
  trois écarts-types : https://www.who.int/tools/elena/interventions/sam-identification-infants
"""

import json
from datetime import date
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Parent
from enfants.models import Enfant
from sib_intelligence.views import (
    calculer_score_triage,
    construire_contexte_systeme,
    reperer_motifs_consultation,
    reperer_signes_danger,
    z_poids_pour_taille,
)

# Libellés exacts renvoyés par reperer_signes_danger().
SIGNE_CONVULSIONS = 'convulsions pendant la maladie actuelle'
SIGNE_EVEIL = 'enfant léthargique ou inconscient'
SIGNE_ALIMENTATION = 'incapable de boire ou de prendre le sein'
SIGNE_VOMISSEMENT = 'vomit tout ce qu\u2019il consomme'
SIGNE_RESPIRATION = 'difficulté respiratoire'
SIGNE_BRAS = 'périmètre brachial inférieur à 11,5 cm'
SIGNE_POIDS_TAILLE = ('poids pour la taille inférieur à moins trois '
                      'écarts-types, malnutrition aiguë sévère')

MOTIF_BRAS = ('périmètre brachial entre 11,5 et 12,5 cm, '
              'malnutrition aiguë modérée')
MOTIF_POIDS_TAILLE = ('poids pour la taille entre moins deux et moins trois '
                      'écarts-types, malnutrition aiguë modérée')

MENTION_SIGNE_UNIQUE = ('Un seul de ces signes suffit à imposer une prise en '
                        'charge immédiate, quels que soient les autres '
                        'symptômes.')

# Poids pour la taille d'un garçon de 18 mois pour 80 cm, d'après les tables
# LMS OMS embarquées : médiane 10,5 kg, moins deux écarts-types 8,9 kg,
# moins trois écarts-types 8,3 kg.
SEVERE = {'sexe': 'M', 'poids': '8.0', 'taille': '80'}
MODEREE = {'sexe': 'M', 'poids': '8.6', 'taille': '80'}
NORMAL = {'sexe': 'M', 'poids': '10.5', 'taille': '80'}


def _naissance_il_y_a_mois(mois):
    """Une date de naissance qui donne exactement `mois` mois d'âge.

    La vue calcule l'âge en mois calendaires, sans tenir compte du jour du
    mois : la date est donc construite mois par mois pour rester déterministe.
    """
    aujourd_hui = date.today()
    annee, index_mois = divmod(
        aujourd_hui.year * 12 + (aujourd_hui.month - 1) - mois, 12)
    return date(annee, index_mois + 1, min(aujourd_hui.day, 28))


class SignesGenerauxDeDangerIsolesTests(TestCase):
    """Un test par signe de danger pris isolément : chacun doit donner rouge."""

    def test_convulsions_isolees(self):
        niveau, message, score, signes = calculer_score_triage(
            {'convulsions': 'oui'}, age_mois=18)
        self.assertEqual(niveau, 'rouge')
        self.assertEqual(signes, [SIGNE_CONVULSIONS])
        self.assertIn('immédiate', message)

    def test_enfant_inconscient_isole(self):
        niveau, _, _, signes = calculer_score_triage(
            {'eveil': 'non'}, age_mois=18)
        self.assertEqual(niveau, 'rouge')
        self.assertEqual(signes, [SIGNE_EVEIL])

    def test_enfant_lethargique_isole(self):
        """La léthargie est un signe de danger au même titre que le coma."""
        niveau, _, _, signes = calculer_score_triage(
            {'eveil': 'difficile'}, age_mois=18)
        self.assertEqual(niveau, 'rouge')
        self.assertEqual(signes, [SIGNE_EVEIL])

    def test_incapable_de_boire_isole(self):
        niveau, _, _, signes = calculer_score_triage(
            {'alimentation': 'refuse'}, age_mois=18)
        self.assertEqual(niveau, 'rouge')
        self.assertEqual(signes, [SIGNE_ALIMENTATION])

    def test_vomit_tout_ce_qu_il_consomme_isole(self):
        niveau, _, _, signes = calculer_score_triage(
            {'vomissement': 'oui_tout'}, age_mois=18)
        self.assertEqual(niveau, 'rouge')
        self.assertEqual(signes, [SIGNE_VOMISSEMENT])

    def test_difficulte_respiratoire_isolee(self):
        niveau, _, _, signes = calculer_score_triage(
            {'respiration': 'difficile'}, age_mois=18)
        self.assertEqual(niveau, 'rouge')
        self.assertEqual(signes, [SIGNE_RESPIRATION])

    def test_perimetre_brachial_sous_11_5_isole(self):
        niveau, _, _, signes = calculer_score_triage({}, muac='10.5', age_mois=18)
        self.assertEqual(niveau, 'rouge')
        self.assertEqual(signes, [SIGNE_BRAS])

    def test_poids_pour_la_taille_sous_moins_trois_ecarts_types_isole(self):
        niveau, _, _, signes = calculer_score_triage(
            dict(SEVERE), poids=SEVERE['poids'], taille=SEVERE['taille'],
            age_mois=18)
        self.assertEqual(niveau, 'rouge')
        self.assertEqual(signes, [SIGNE_POIDS_TAILLE])

    def test_un_signe_de_danger_prime_sur_un_score_faible(self):
        """Le signe court-circuite le score, il ne s'y additionne pas."""
        _, _, _, signes = calculer_score_triage({'convulsions': 'oui'}, age_mois=18)
        self.assertEqual(len(signes), 1)
        niveau, _, score, _ = calculer_score_triage(
            {'convulsions': 'oui', 'fievre': 'oui_moderee'}, age_mois=18)
        self.assertEqual(niveau, 'rouge')
        self.assertLess(score, 6)

    def test_plusieurs_signes_sont_tous_listes(self):
        symptomes = {'convulsions': 'oui', 'respiration': 'difficile',
                     'alimentation': 'refuse'}
        niveau, _, _, signes = calculer_score_triage(symptomes, age_mois=18)
        self.assertEqual(niveau, 'rouge')
        self.assertEqual(len(signes), 3)

    def test_la_fonction_renvoie_un_quadruplet(self):
        resultat = calculer_score_triage({}, age_mois=18)
        self.assertEqual(len(resultat), 4)
        niveau, message, score, signes = resultat
        self.assertEqual(niveau, 'vert')
        self.assertEqual(score, 0)
        self.assertEqual(signes, [])

    def test_reperer_signes_danger_liste_les_sept_signes_de_la_pcime(self):
        """Chaque signe de la liste PCIME doit être repérable seul."""
        cas = [
            ({'convulsions': 'oui'}, SIGNE_CONVULSIONS),
            ({'eveil': 'difficile'}, SIGNE_EVEIL),
            ({'eveil': 'non'}, SIGNE_EVEIL),
            ({'alimentation': 'refuse'}, SIGNE_ALIMENTATION),
            ({'vomissement': 'oui_tout'}, SIGNE_VOMISSEMENT),
            ({'respiration': 'difficile'}, SIGNE_RESPIRATION),
        ]
        for symptomes, attendu in cas:
            with self.subTest(symptomes=symptomes):
                self.assertEqual(reperer_signes_danger(symptomes, None, 18),
                                 [attendu])


class PerimetreBrachialTests(TestCase):
    """Seuils OMS et UNICEF 2009 : 115 mm et 125 mm, de 6 à 59 mois."""

    def test_11_5_exactement_ne_declenche_pas_le_signe_de_danger(self):
        niveau, _, _, signes = calculer_score_triage({}, muac='11.5', age_mois=18)
        self.assertEqual(signes, [])
        self.assertNotEqual(niveau, 'rouge')
        self.assertEqual(niveau, 'jaune')
        self.assertEqual(reperer_motifs_consultation({}, '11.5', 18), [MOTIF_BRAS])

    def test_11_4_declenche_le_signe_de_danger(self):
        niveau, _, _, signes = calculer_score_triage({}, muac='11.4', age_mois=18)
        self.assertEqual(niveau, 'rouge')
        self.assertEqual(signes, [SIGNE_BRAS])

    def test_12_0_donne_au_minimum_jaune(self):
        """Une malnutrition aiguë modérée ne se règle pas à domicile."""
        niveau, _, _, signes = calculer_score_triage({}, muac='12.0', age_mois=18)
        self.assertEqual(signes, [])
        self.assertEqual(niveau, 'jaune')

    def test_12_5_exactement_reste_vert(self):
        niveau, _, _, signes = calculer_score_triage({}, muac='12.5', age_mois=6)
        self.assertEqual(niveau, 'vert')
        self.assertEqual(signes, [])
        self.assertEqual(reperer_motifs_consultation({}, '12.5', 6), [])

    def test_6_mois_et_59_mois_sont_dans_la_fenetre(self):
        for age in (6, 59):
            with self.subTest(age_mois=age):
                self.assertEqual(reperer_signes_danger({}, '10.5', age),
                                 [SIGNE_BRAS])

    def test_perimetre_brachial_a_trois_mois_est_ignora(self):
        """Avant 6 mois, la mesure ne permet aucune conclusion."""
        niveau, _, _, signes = calculer_score_triage({}, muac='10.5', age_mois=3)
        self.assertEqual(niveau, 'vert')
        self.assertEqual(signes, [])
        self.assertEqual(reperer_motifs_consultation({}, '10.5', 3), [])

    def test_perimetre_brachial_a_72_mois_est_ignora(self):
        niveau, _, _, signes = calculer_score_triage({}, muac='10.5', age_mois=72)
        self.assertEqual(niveau, 'vert')
        self.assertEqual(signes, [])
        self.assertEqual(reperer_motifs_consultation({}, '10.5', 72), [])

    def test_perimetre_brachial_non_numerique_ne_fait_pas_planter(self):
        for valeur in ('abc', '11,5', 'onze', '', '   ', None):
            with self.subTest(muac=valeur):
                niveau, _, _, signes = calculer_score_triage(
                    {}, muac=valeur, age_mois=18)
                self.assertEqual(niveau, 'vert')
                self.assertEqual(signes, [])

    def test_perimetre_brachial_sans_age_connu_est_lu_par_prudence(self):
        """Âge inconnu : la mesure est lue, par prudence, comme après 6 mois."""
        signes = reperer_signes_danger({}, '10.5', None)
        self.assertEqual(signes, [SIGNE_BRAS])


class PoidsPourLaTailleTests(TestCase):
    """L'indicateur OMS remplace l'IMC brut et ses seuils fixes de 14 et 16."""

    def test_l_imc_brut_ne_classe_plus_rien(self):
        """6 kg pour 80 cm donnait 3 points par IMC : sans sexe, ignoré."""
        niveau, _, _, signes = calculer_score_triage(
            {}, poids='6', taille='80', age_mois=18)
        self.assertEqual(niveau, 'vert')
        self.assertEqual(signes, [])

    def test_sexe_absent_fait_ignorer_l_indicateur(self):
        symptomes = {'poids': '8.0', 'taille': '80'}
        self.assertIsNone(z_poids_pour_taille(symptomes, 18))
        niveau, _, _, signes = calculer_score_triage(
            symptomes, poids='8.0', taille='80', age_mois=18)
        self.assertEqual(niveau, 'vert')
        self.assertEqual(signes, [])

    def test_sexe_vide_fait_ignorer_l_indicateur(self):
        symptomes = {'sexe': '', 'poids': '8.0', 'taille': '80'}
        self.assertIsNone(z_poids_pour_taille(symptomes, 18))

    def test_age_absent_fait_ignorer_l_indicateur(self):
        symptomes = {'sexe': 'M', 'poids': '8.0', 'taille': '80'}
        self.assertIsNone(z_poids_pour_taille(symptomes, None))
        niveau, _, _, signes = calculer_score_triage(
            symptomes, poids='8.0', taille='80', age_mois=None)
        self.assertEqual(niveau, 'vert')
        self.assertEqual(signes, [])

    def test_poids_ou_taille_absent_fait_ignorer_l_indicateur(self):
        for symptomes in ({'sexe': 'M', 'taille': '80'},
                          {'sexe': 'M', 'poids': '8.0'},
                          {'sexe': 'M'}):
            with self.subTest(symptomes=symptomes):
                self.assertIsNone(z_poids_pour_taille(symptomes, 18))

    def test_valeurs_non_numeriques_ne_font_pas_planter(self):
        for symptomes in ({'sexe': 'M', 'poids': 'huit', 'taille': '80'},
                          {'sexe': 'M', 'poids': '8.0', 'taille': 'inconnue'},
                          {'sexe': 'M', 'poids': '0', 'taille': '0'}):
            with self.subTest(symptomes=symptomes):
                self.assertIsNone(z_poids_pour_taille(symptomes, 18))

    def test_tables_oms_absentes_ne_font_pas_planter(self):
        with mock.patch('sib_intelligence.views.z_poids_taille', None):
            self.assertIsNone(z_poids_pour_taille(dict(SEVERE), 18))
            niveau, _, _, signes = calculer_score_triage(
                dict(SEVERE), poids=SEVERE['poids'], taille=SEVERE['taille'],
                age_mois=18)
        self.assertEqual(niveau, 'vert')
        self.assertEqual(signes, [])

    def test_le_sexe_change_la_lecture_du_poids_pour_la_taille(self):
        """8,0 kg pour 80 cm à 18 mois : sévère chez le garçon, pas chez la fille."""
        garcon = z_poids_pour_taille(
            {'sexe': 'M', 'poids': '8.0', 'taille': '80'}, 18)
        fille = z_poids_pour_taille(
            {'sexe': 'F', 'poids': '8.0', 'taille': '80'}, 18)
        self.assertLess(garcon, -3)
        self.assertLess(garcon, fille)
        self.assertGreaterEqual(fille, -3)
        self.assertLess(fille, -2)

    def test_z_sous_moins_trois_donne_rouge(self):
        self.assertLess(z_poids_pour_taille(dict(SEVERE), 18), -3)
        self.assertEqual(reperer_signes_danger(dict(SEVERE), None, 18),
                         [SIGNE_POIDS_TAILLE])

    def test_z_entre_moins_trois_et_moins_deux_donne_jaune(self):
        z = z_poids_pour_taille(dict(MODEREE), 18)
        self.assertLess(-3, z)
        self.assertLess(z, -2)
        self.assertEqual(reperer_signes_danger(dict(MODEREE), None, 18), [])
        self.assertEqual(reperer_motifs_consultation(dict(MODEREE), None, 18),
                         [MOTIF_POIDS_TAILLE])
        niveau, _, _, _ = calculer_score_triage(
            dict(MODEREE), poids=MODEREE['poids'], taille=MODEREE['taille'],
            age_mois=18)
        self.assertEqual(niveau, 'jaune')

    def test_z_au_dessus_de_moins_deux_reste_vert(self):
        self.assertGreaterEqual(z_poids_pour_taille(dict(NORMAL), 18), -2)
        niveau, _, _, signes = calculer_score_triage(
            dict(NORMAL), poids=NORMAL['poids'], taille=NORMAL['taille'],
            age_mois=18)
        self.assertEqual(niveau, 'vert')
        self.assertEqual(signes, [])


class VomissementsTests(TestCase):
    """La PCIME distingue l'enfant qui garde des liquides de celui qui ne garde rien."""

    def test_vomissements_repetes_qui_gardent_des_liquides_restent_verts(self):
        niveau, _, _, signes = calculer_score_triage(
            {'vomissement': 'oui_repete'}, age_mois=18)
        self.assertEqual(niveau, 'vert')
        self.assertEqual(signes, [])

    def test_quelques_vomissements_restent_verts(self):
        niveau, _, _, signes = calculer_score_triage(
            {'vomissement': 'oui_simple'}, age_mois=18)
        self.assertEqual(niveau, 'vert')
        self.assertEqual(signes, [])

    def test_vomit_tout_donne_rouge_alors_que_repete_donne_vert(self):
        dangereux, _, _, signes = calculer_score_triage(
            {'vomissement': 'oui_tout'}, age_mois=18)
        non_dangereux, _, _, _ = calculer_score_triage(
            {'vomissement': 'oui_repete'}, age_mois=18)
        self.assertEqual(dangereux, 'rouge')
        self.assertEqual(signes, [SIGNE_VOMISSEMENT])
        self.assertEqual(non_dangereux, 'vert')


class ScoreResiduelTests(TestCase):
    """Le score ne porte plus que sur les symptômes gradués non urgents."""

    def test_fievre_haute_et_diarrhee_sanglante_donnent_rouge(self):
        niveau, _, score, signes = calculer_score_triage(
            {'fievre': 'oui_haute', 'diarrhee': 'oui_sang'}, age_mois=18)
        self.assertEqual(score, 6)
        self.assertEqual(niveau, 'rouge')
        self.assertEqual(signes, [])

    def test_fievre_moderee_seule_donne_jaune(self):
        niveau, _, score, _ = calculer_score_triage(
            {'fievre': 'oui_moderee', 'respiration': 'rapide'}, age_mois=18)
        self.assertEqual(score, 3)
        self.assertEqual(niveau, 'jaune')

    def test_enfant_sans_symptome_donne_vert(self):
        niveau, message, score, signes = calculer_score_triage({}, age_mois=18)
        self.assertEqual((niveau, score, signes), ('vert', 0, []))
        self.assertIn('domicile', message)

    def test_les_messages_ne_contiennent_ni_emoji_ni_tiret_cadratin(self):
        messages = [
            calculer_score_triage({'convulsions': 'oui'}, age_mois=18)[1],
            calculer_score_triage({'fievre': 'oui_haute'}, age_mois=18)[1],
            calculer_score_triage({}, age_mois=18)[1],
        ]
        for message in messages:
            with self.subTest(message=message):
                self.assertFalse([c for c in message if ord(c) > 0x2100])
                self.assertNotIn('\u2014', message)
                self.assertNotIn('\u2192', message)


class FormulaireTriageTests(TestCase):
    """Le formulaire doit poser les questions dans les termes de la PCIME."""

    def setUp(self):
        self.html = self.client.get('/triage/').content.decode('utf-8')

    def test_le_formulaire_propose_un_champ_sexe_avec_option_vide(self):
        self.assertIn('name="sexe"', self.html)
        bloc = self.html.split('name="sexe"')[1].split('</select>')[0]
        self.assertIn('<option value="">', bloc)
        self.assertIn('<option value="M">', bloc)
        self.assertIn('<option value="F">', bloc)
        self.assertLess(bloc.index('<option value="">'), bloc.index('<option value="M">'))

    def test_deux_reponses_distinctes_pour_les_vomissements(self):
        self.assertIn('value="oui_repete">Répétés, mais garde des liquides',
                      self.html)
        self.assertIn('value="oui_tout">Vomit tout ce qu\'il consomme',
                      self.html)

    def test_formulation_des_questions_de_danger(self):
        attendus = [
            'value="refuse">Incapable de boire ou de téter',
            'value="difficile">Difficile, tirage ou geignement',
            'value="oui">Oui, pendant cette maladie',
            'value="difficile">Léthargique, anormalement endormi',
            'value="non">Inconscient, ne réagit pas',
        ]
        for attendu in attendus:
            with self.subTest(option=attendu):
                self.assertIn(attendu, self.html)

    def test_le_perimetre_brachial_est_annonce_de_6_a_59_mois(self):
        self.assertIn('Périmètre brachial (cm)', self.html)
        self.assertIn('6 à 59 mois', self.html)

    def test_la_page_rappelle_la_regle_du_signe_unique(self):
        self.assertIn('un seul signe général de danger impose une prise en '
                      'charge immédiate', self.html)


class VueTriageTests(TestCase):
    """Bout en bout : la vue propage l'âge et le sexe, puis affiche les signes."""

    def test_post_avec_une_convulsion_isolee_donne_rouge(self):
        reponse = self.client.post('/triage/', {
            'prenom': 'Kofi', 'age_mois': '18', 'convulsions': 'oui',
        })
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.context['niveau'], 'rouge')
        self.assertEqual(reponse.context['signes'], [SIGNE_CONVULSIONS])
        self.assertContains(reponse, MENTION_SIGNE_UNIQUE)
        self.assertContains(reponse, SIGNE_CONVULSIONS)

    def test_les_signes_sont_listes_sous_le_message(self):
        reponse = self.client.post('/triage/', {
            'age_mois': '18', 'respiration': 'difficile',
            'alimentation': 'refuse',
        })
        html = reponse.content.decode('utf-8')
        self.assertIn('Signes de danger relevés', html)
        self.assertIn(SIGNE_RESPIRATION, html)
        self.assertIn(SIGNE_ALIMENTATION, html)
        self.assertLess(html.index('Urgence immédiate'),
                        html.index('Signes de danger relevés'))

    def test_aucune_liste_de_signes_quand_le_niveau_est_vert(self):
        reponse = self.client.post('/triage/', {
            'age_mois': '18', 'vomissement': 'oui_repete',
        })
        self.assertEqual(reponse.context['niveau'], 'vert')
        self.assertEqual(reponse.context['signes'], [])
        self.assertNotContains(reponse, 'Signes de danger relevés')

    def test_l_age_et_le_sexe_sont_propages_jusqu_au_poids_pour_la_taille(self):
        reponse = self.client.post('/triage/', {
            'age_mois': '18', 'sexe': 'M', 'poids': '8.0', 'taille': '80',
        })
        self.assertEqual(reponse.context['niveau'], 'rouge')
        self.assertEqual(reponse.context['signes'], [SIGNE_POIDS_TAILLE])

    def test_le_perimetre_brachial_d_un_nourrisson_de_trois_mois_est_ignora(self):
        reponse = self.client.post('/triage/', {
            'age_mois': '3', 'muac': '10.5',
        })
        self.assertEqual(reponse.context['niveau'], 'vert')
        self.assertEqual(reponse.context['signes'], [])

    def test_sexe_absent_en_vue_fait_ignorer_le_poids_pour_la_taille(self):
        reponse = self.client.post('/triage/', {
            'age_mois': '18', 'poids': '8.0', 'taille': '80',
        })
        self.assertEqual(reponse.context['niveau'], 'vert')
        self.assertEqual(reponse.context['signes'], [])

    def test_age_absent_ne_fait_pas_planter_la_vue(self):
        reponse = self.client.post('/triage/', {'muac': '12.0'})
        self.assertEqual(reponse.status_code, 200)
        self.assertIsNone(reponse.context['age_mois'])
        self.assertNotContains(reponse, 'None mois')

    def test_age_illisible_ne_fait_pas_planter_la_vue(self):
        reponse = self.client.post('/triage/', {
            'age_mois': 'dix-huit', 'fievre': 'oui_haute',
        })
        self.assertEqual(reponse.status_code, 200)
        self.assertIsNone(reponse.context['age_mois'])
        self.assertEqual(reponse.context['niveau'], 'jaune')

    def test_perimetre_brachial_non_numerique_en_vue_ne_fait_pas_planter(self):
        reponse = self.client.post('/triage/', {'age_mois': '18', 'muac': 'abc'})
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.context['niveau'], 'vert')

    def test_l_age_du_dossier_est_utilise_pour_le_perimetre_brachial(self):
        user = User.objects.create_user(username='papa@test.bj',
                                        password='MotDePasse123')
        parent = Parent.objects.create(user=user, telephone='97000001')
        Enfant.objects.create(parent=parent, nom='Koffi', prenom='Kofi',
                              date_naissance=_naissance_il_y_a_mois(18),
                              sexe='M')
        enfant = Enfant.objects.get(prenom='Kofi')
        self.client.login(username='papa@test.bj', password='MotDePasse123')
        reponse = self.client.post('/triage/', {
            'enfant_id': enfant.id, 'muac': '11.0',
        })
        self.assertEqual(reponse.context['age_mois'], 18)
        self.assertEqual(reponse.context['niveau'], 'rouge')
        self.assertEqual(reponse.context['signes'], [SIGNE_BRAS])

    def test_les_signes_sont_transmis_au_contexte_de_l_assistant(self):
        reponse = self.client.post('/triage/', {
            'age_mois': '18', 'convulsions': 'oui',
        })
        contexte = reponse.context['contexte']
        self.assertEqual(contexte['signes_danger'], [SIGNE_CONVULSIONS])
        self.assertIn('signes_danger', reponse.content.decode('utf-8'))
        self.assertIn(SIGNE_CONVULSIONS, reponse.content.decode('utf-8'))

    def test_le_formulaire_accepte_le_champ_sexe(self):
        from sib_intelligence.views import _symptomes_from_post
        symptomes = _symptomes_from_post({'sexe': 'F', 'poids': '8.0'})
        self.assertEqual(symptomes['sexe'], 'F')


class PromptAssistantTests(TestCase):
    """L'assistant doit nommer les signes de danger au parent en mots simples."""

    def test_les_signes_sont_transmis_au_prompt_avec_la_consigne(self):
        prompt = construire_contexte_systeme(
            enfant_nom='Kofi', age_mois=18, niveau='rouge',
            message='Urgence immédiate', symptomes={},
            signes_danger=[SIGNE_CONVULSIONS, SIGNE_RESPIRATION],
        )
        self.assertIn(SIGNE_CONVULSIONS, prompt)
        self.assertIn(SIGNE_RESPIRATION, prompt)
        self.assertIn('Un seul de ces signes suffit', prompt)
        self.assertIn('en mots simples', prompt)

    def test_sans_signe_le_prompt_le_dit_explicitement(self):
        prompt = construire_contexte_systeme(
            enfant_nom='Kofi', age_mois=18, niveau='vert',
            message='Conseils à domicile', symptomes={}, signes_danger=[],
        )
        self.assertIn('Signes généraux de danger relevés : aucun', prompt)
        self.assertNotIn(SIGNE_CONVULSIONS, prompt)

    def test_un_age_absent_ne_donne_pas_none_mois_dans_le_prompt(self):
        prompt = construire_contexte_systeme(
            enfant_nom='Kofi', age_mois='non précisé', niveau='vert',
            message='Conseils à domicile', symptomes={},
        )
        self.assertIn('- Âge : non précisé', prompt)
        self.assertNotIn('None mois', prompt)
        prompt = construire_contexte_systeme(
            enfant_nom='Kofi', age_mois=18, niveau='vert',
            message='Conseils à domicile', symptomes={},
        )
        self.assertIn('- Âge : 18 mois', prompt)

    def test_le_prompt_reste_construit_sans_parametre_signes(self):
        prompt = construire_contexte_systeme(
            enfant_nom='Kofi', age_mois=18, niveau='jaune',
            message='Consultation recommandée', symptomes={},
        )
        self.assertIn('Signes généraux de danger relevés : aucun', prompt)


class ChatAssistantTests(TestCase):
    """Le point d'entrée du chat doit transmettre les signes au prompt système."""

    def _faux_client(self, prompts):
        """Un client Groq de substitution qui enregistre le prompt système."""

        class FauxCompletions:
            def create(self, **parametres):
                prompts.append(parametres['messages'][0]['content'])
                choix = SimpleNamespace(
                    message=SimpleNamespace(content='Réponse de test'))
                return SimpleNamespace(choices=[choix])

        return SimpleNamespace(
            chat=SimpleNamespace(completions=FauxCompletions()))

    def _poster(self, contexte):
        return self.client.post(
            '/triage/chat/',
            data=json.dumps({'message': 'Que dois-je faire ?',
                             'contexte': contexte}),
            content_type='application/json',
        )

    def test_les_signes_de_danger_arrivent_dans_le_prompt_du_chat(self):
        prompts = []
        with mock.patch('sib_intelligence.views._client_groq',
                        return_value=self._faux_client(prompts)):
            reponse = self._poster({
                'enfant_nom': 'Kofi', 'age_mois': 18, 'niveau': 'rouge',
                'message': 'Urgence immédiate',
                'signes_danger': [SIGNE_CONVULSIONS, SIGNE_RESPIRATION],
                'symptomes': {'convulsions': 'oui', 'sexe': 'M'},
            })
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.json()['suggestion'], 'hospital')
        self.assertEqual(len(prompts), 1)
        self.assertIn(SIGNE_CONVULSIONS, prompts[0])
        self.assertIn(SIGNE_RESPIRATION, prompts[0])
        self.assertIn('Un seul de ces signes suffit', prompts[0])
        self.assertIn('en mots simples', prompts[0])
        self.assertIn('Sexe : M', prompts[0])

    def test_le_chat_sans_cle_api_ne_fait_pas_planter_les_signes(self):
        with mock.patch('sib_intelligence.views._client_groq', return_value=None):
            reponse = self._poster({
                'niveau': 'rouge', 'signes_danger': [SIGNE_CONVULSIONS],
            })
        self.assertEqual(reponse.status_code, 200)
        donnees = reponse.json()
        self.assertEqual(donnees['status'], 'ok')
        self.assertIn('professionnel de santé', donnees['reponse'])

    def test_un_contexte_sans_signes_ne_fait_pas_planter_le_chat(self):
        prompts = []
        with mock.patch('sib_intelligence.views._client_groq',
                        return_value=self._faux_client(prompts)):
            reponse = self._poster({'niveau': 'vert', 'symptomes': {}})
        self.assertEqual(reponse.status_code, 200)
        self.assertIn('relevés : aucun', prompts[0])
