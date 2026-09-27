"""Contenu des fichiers /llms.txt et /llms-full.txt (indexation par les assistants IA).

Format proposé par llmstxt.org : le premier fichier est un sommaire hiérarchique,
le second contient l'intégralité du contenu public utile du site en Markdown.
"""
from sante.models import Etablissement


def nb_structures():
    """Nombre de structures de santé chargées (842 après le seed standard)."""
    try:
        return Etablissement.objects.count() or 842
    except Exception:
        return 842


# ---------------------------------------------------------------------------
# /llms.txt : sommaire
# ---------------------------------------------------------------------------
def llms_txt(request):
    base = f"https://{request.get_host()}"
    nb = nb_structures()
    return f"""# Santé Infantile Bénin

> Plateforme web gratuite (PWA) de suivi de la santé des nourrissons et jeunes enfants de 0 à 5 ans au Bénin : calendrier vaccinal officiel PEV, conseils nutritionnels par âge, dépistage de la malnutrition par Z-scores OMS, premiers secours et carte de {nb} structures de santé. Contenu en français, destiné aux parents et agents de santé. Éditée par SOSSA Gninazé Mingnissê Darius, infirmier diplômé d'État.

Informations essentielles :
- Urgences médicales au Bénin : 112 (SAMU, gratuit, 24h/24, tous réseaux) · Pompiers : 118 · Police : 117.
- Les outils (vaccination, nutrition, dépistage, secours, carte) sont utilisables sans créer de compte.
- Le site ne délivre pas de diagnostic : en cas de signe de danger, il oriente vers le 112 ou le centre de santé le plus proche.
- Le contenu complet du site est disponible sur {base}/llms-full.txt.

## Outils santé

- [Calendrier vaccinal PEV Bénin]({base}/conseils/): calendrier officiel du Programme Élargi de Vaccination (BCG, VPO, hépatite B, pentavalent, PCV, rotavirus, rougeole, fièvre jaune, méningite A) avec dates prévues selon la date de naissance.
- [Calculateur de rendez-vous vaccinaux]({base}/conseils/rdv/): génère le planning vaccinal d'un enfant à partir de sa date de naissance.
- [Conseils nutritionnels par âge]({base}/conseils/nutrition/): allaitement, diversification, aliments locaux du Bénin, prévention de l'anémie et de la malnutrition, de 0 à 10 ans.
- [Dépistage de la malnutrition (Z-scores OMS)]({base}/depistage/): évaluation du poids, de la taille et du périmètre brachial selon les standards de croissance OMS (indicateurs poids-pour-âge, taille-pour-âge, poids-pour-taille, MUAC 11,5/12,5 cm).
- [Premiers secours & signes de danger]({base}/premiers-secours/): signes d'urgence et gestes de secours de 0 à 5 ans (fièvre, convulsions, étouffement, diarrhée, brûlures, plaies, morsures, noyade...), d'après le mémento pédiatrique OMS et la PCIME.
- [Carte des structures de santé]({base}/carte/): {nb} centres de santé, hôpitaux, cliniques et pharmacies du Bénin géolocalisés, avec itinéraire.
- [Triage pédiatrique assisté par IA]({base}/triage/): orientation rapide selon les symptômes saisis (nécessite une connexion internet).

## Pages générales

- [Accueil]({base}/): présentation des outils et des urgences.
- [À propos]({base}/a-propos/): l'éditeur, la mission et les références du projet.
- [Inscription]({base}/inscription/): création d'un compte parent gratuit (numéro de téléphone).
- [Connexion]({base}/connexion/): accès à l'espace parent.

## Pages légales

- [Politique de confidentialité]({base}/politique-de-confidentialite/): données collectées, finalités, durées, droits (Code du numérique du Bénin, loi n° 2017-20, APDP).
- [Politique des cookies]({base}/politique-des-cookies/): cookies techniques uniquement, aucun traceur publicitaire.
- [Conditions d'utilisation]({base}/cgu/): conditions générales d'utilisation du service.

## Ressources techniques

- [Mode hors-ligne]({base}/hors-ligne/): page de repli de l'application installable (PWA) ; tous les outils fonctionnent sans réseau une fois l'application installée.
- [robots.txt]({base}/robots.txt): règles d'exploration (assistants IA autorisés sur les pages publiques).
- [sitemap.xml]({base}/sitemap.xml): plan du site.
"""


# ---------------------------------------------------------------------------
# /llms-full.txt : contenu intégral
# ---------------------------------------------------------------------------
def llms_full_txt(request):
    base = f"https://{request.get_host()}"
    nb = nb_structures()
    return f"""# Santé Infantile Bénin — contenu intégral

> Plateforme web gratuite (PWA) de suivi de la santé des nourrissons et jeunes enfants de 0 à 5 ans au Bénin. Contenu en français. URL : {base}/

## 0. Informations essentielles

- **Urgences médicales au Bénin : 112 (SAMU Bénin)** — appel gratuit, disponible 24h/24, fonctionne sur tous les réseaux même sans crédit.
- **Sapeurs-pompiers : 118** — accidents, incendies, secours aux personnes. Gratuit, 24h/24.
- **Police républicaine : 117** — numéro vert, gratuit, 24h/24 et 7j/7.
- Éditeur : SOSSA Gninazé Mingnissê Darius, infirmier diplômé d'État et développeur, Cotonou, Bénin. Contact : sante.infantile.benin@gmail.com · WhatsApp : +229 01 98 41 92 40.
- Le site est une aide éducative : il ne remplace jamais l'avis d'un professionnel de santé.
- Avant de partir au centre de santé : prendre le carnet de vaccination de l'enfant, garder le nourrisson contre soi pour le réchauffer, continuer l'allaitement si possible, et signaler tout médicament déjà donné.

## 1. Vaccination — calendrier officiel PEV Bénin

Page : {base}/conseils/ · Calculateur de rendez-vous : {base}/conseils/rdv/

Le Programme Élargi de Vaccination (PEV) du Bénin recommande, selon l'âge de l'enfant (compter en semaines à partir de la date de naissance) :

**À la naissance (semaine 0) :**
- BCG (tuberculose), dose unique
- VPO 0 (poliomyélite orale, dose de naissance)
- Vaccin contre l'hépatite B (dose de naissance)

**À partir de 6 semaines :**
- Pentavalent (DTC-HepB-Hib) doses 1, 2 et 3 — âges minimaux 6, 10 et 14 semaines, intervalle minimal de 4 semaines entre deux doses
- VPO (polio orale) doses 1, 2 et 3 — 6, 10 et 14 semaines
- PCV (pneumocoque) doses 1, 2 et 3 — 6, 10 et 14 semaines

**À partir de 22 semaines (environ 5 mois et demi) :**
- RTSS (rotavirus) doses 1 et 2 — 22 et 26 semaines

**À 39 semaines (environ 9 mois) :**
- VAR (rougeole), dose unique
- VAA (fièvre jaune), dose unique
- MenA (méningite à méningocoque A), dose unique
- RTSS dose 3

**À 65 semaines (environ 15 mois) :**
- RTSS dose 4

Le site calcule automatiquement les dates prévues à partir de la date de naissance saisie et signale les rappels en retard. Le carnet de vaccination reste le document de référence.

## 2. Nutrition infantile par âge

Page : {base}/conseils/nutrition/

**0 à 6 mois :**
- Allaitement maternel exclusif pendant les 6 premiers mois (recommandation OMS) : le lait maternel couvre tous les besoins et protège contre les infections ; aucun autre aliment ni liquide n'est nécessaire.
- Le colostrum (premier lait, jaune et épais) est précieux : riche en anticorps, ne jamais le jeter.
- Téter à la demande, au moins 8 à 12 fois par 24 heures ; les tétées nocturnes sont importantes.
- Diarrhée : continuer l'allaitement, donner des SRO (sels de réhydratation orale), consulter si elle dure plus de 3 jours ou si l'enfant montre des signes de déshydratation.
- Fièvre : augmenter les tétées ; consulter immédiatement si elle dépasse 38,5 °C chez un nourrisson de moins de 3 mois ; jamais d'aspirine.

**6 à 12 mois :**
- Introduire progressivement les aliments complémentaires en continuant l'allaitement : purées lisses de légumes, céréales et fruits ; un seul aliment nouveau à la fois (attendre 3 jours).
- Les réserves en fer s'épuisent vers 6 mois : introduire viande mixée, foie de volaille, haricots, lentilles, légumes verts (prévention de l'anémie).
- Textures : 6-7 mois purées très lisses ; 7-8 mois petits morceaux mixés ; 8-10 mois écrasés à la fourchette ; 10-12 mois petits morceaux tendres.

**12 à 24 mois :**
- 3 repas par jour plus 2 collations ; poursuivre l'allaitement jusqu'à 2 ans et au-delà si possible.
- Éviter le sel ajouté et le sucre raffiné ; l'eau est la meilleure boisson.
- Signes d'alerte de malnutrition : poids insuffisant, œdèmes des pieds, cheveux roux et cassants, ventre gonflé, enfant apathique, périmètre brachial (MUAC) inférieur à 11,5 cm — consulter immédiatement.

**2 à 5 ans :**
- 3 repas équilibrés (énergie : céréales ; protéines : viande, poisson, œufs, légumineuses ; légumes et fruits) plus 1 à 2 collations.
- Vitamine A : huile de palme rouge, patate douce orange, mangue, papaye, feuilles vertes, foie ; supplementation recommandée tous les 6 mois.
- Aliments locaux nutritifs : gari, akassa, ablo (énergie), haricots et niébé (protéines), feuilles de moringa (fer, vitamines), huile de palme rouge (vitamine A), poisson fumé (protéines, oméga-3).
- Déparasitage recommandé tous les 6 mois ; lavage des mains avant les repas et après les toilettes.
- Limiter aliments ultra-transformés et sucres pour prévenir le surpoids.

## 3. Dépistage de la malnutrition (Z-scores OMS)

Page : {base}/depistage/

L'outil évalue l'état nutritionnel d'un enfant de 0 à 5 ans à partir de son âge, de son sexe, de son poids, de sa taille et éventuellement de son périmètre brachial (MUAC).

- Indicateurs calculés selon les standards de croissance OMS (méthode LMS : Z = ((X/M)^L − 1) / (L × S)) : poids-pour-âge, taille-pour-âge, poids-pour-taille.
- Lecture pour les parents : un indicateur sous la ligne −2 (ambre) demande un avis au centre de santé ; sous la ligne −3 (rouge), la consultation est immédiate.
- Périmètre brachial (MUAC) : seuils OMS/UNICEF 11,5 cm (malnutrition aiguë sévère) et 12,5 cm (modérée).
- Mesures fiables : enfant légèrement vêtu, balance tarée, taille mesurée debout (≥ 2 ans) ou couchée (< 2 ans), brassard MUAC à mi-hauteur du bras gauche.
- L'outil est une aide au repérage, pas un dossier clinique : tout doute impose une consultation.

## 4. Premiers secours et signes de danger (0-5 ans)

Page : {base}/premiers-secours/

**Signes d'urgence — partir immédiatement au centre de santé ou appeler le 112 :**
- Coma, perte de conscience, convulsions
- Détresse respiratoire grave, lèvres ou langue bleues
- Signes de choc (pâleur extrême, extrémités froides, pouls rapide et faible)
- Déshydratation sévère (yeux creux, pli cutané persistant, somnolence, boit très mal)

**Signes de priorité — consulter le jour même :**
- Nourrisson de moins de 2 mois malade
- Fièvre élevée ou qui dure
- Refus de boire ou vomissements répétés
- Comportement inhabituel (somnolence anormale, geignements constants)
- Pâleur marquée, intoxication, amaigrissement ou gonflements
- Traumatisme ou brûlure étendue, douleurs intenses

**Gestes par situation (résumés) :**
- Fièvre : découvrir l'enfant, boire souvent, paracétamol selon le poids ; jamais d'aspirine chez l'enfant. Consulter si fièvre > 38,5 °C avant 3 mois.
- Convulsions : allonger l'enfant sur le côté, rien dans la bouche, écarter les objets dangereux ; après la crise, consulter. Perte de conscience : 112 et massage cardiaque.
- Étouffement : 5 claques dans le dos, puis 5 compressions abdominales (maniœuvre de Heimlich adaptée) ; si l'enfant perd connaissance : 112 et réanimation.
- Diarrhée : SRO immédiatement (un sachet dans l'eau potable recommandée), continuer à nourrir et allaiter ; consulter si signes de déshydratation.
- Brûlures : refroidir à l'eau tiède courante 10-20 minutes, retirer les vêtements non collés, couvrir proprement ; pas de pommades ni huiles ; consulter si étendue ou au visage.
- Plaies : nettoyer à l'eau et au savon, comprimer pour stopper le saignement, couvrir ; plaie profonde ou souillée (terre, morsure) : consulter (risque de tétanos).
- Morsures et piqûres (serpent, chien, scorpion) : immobiliser, ne pas inciser ni aspirer, ne pas poser de garrot, transporter rapidement ; morsure de chien : consulter pour la rage.
- Choc à la tête : surveiller ; vomissements répétés ou somnolence anormale : consulter en urgence.
- Ingestion de produit dangereux : ne pas faire vomir, appeler le centre de santé avec l'emballage ; brûlures de la bouche : urgence immédiate.
- Noyade : sortir de l'eau, vérifier la respiration ; si absente : bouche-à-bouche et massage cardiaque, faire appeler le 112.
- Électrocution : couper le courant avant de toucher l'enfant, puis réanimation si nécessaire.

**Erreurs à ne jamais commettre :** donner un médicament adulte à un enfant, faire boire quelque chose à un enfant inconscient, mettre de l'huile ou de la poudre sur une brûlure, inciser une morsure, poser un garrot, donner de l'aspirine à un nourrisson.

Sources : Mémento de soins hospitaliers pédiatriques de l'OMS (2ᵉ édition) et prise en charge intégrée des maladies de l'enfant (PCIME).

## 5. Carte des structures de santé du Bénin

Page : {base}/carte/

- {nb} structures géolocalisées : centres de santé, hôpitaux, cliniques et pharmacies de l'ensemble du territoire béninois.
- Géolocalisation de l'utilisateur, recherche des 10 structures les plus proches et itinéraire Google Maps.
- Données issues d'OpenStreetMap (contributeurs, ODbL) et enrichies localement ; fonctionne sans appel externe grâce à la base embarquée.

## 6. Triage pédiatrique assisté par IA

Page : {base}/triage/

- L'assistant oriente rapidement selon les signes saisis : niveau vert (conseils à domicile), ambre (consultation rapide), rouge (urgence immédiate).
- Les symptômes sont traités de manière anonyme, sans identifiant personnel.
- Nécessite une connexion internet ; ne remplace pas le 112 ni un examen clinique.

## 7. Espace parent (compte gratuit)

- Inscription : {base}/inscription/ — avec un numéro de téléphone et un mot de passe ; vérification par code SMS possible.
- Espace : {base}/dashboard/ — suivi des enfants (profil, vaccins reçus, rappels à venir), profils multiples.
- Le compte n'est pas nécessaire pour utiliser les outils publics (vaccination, nutrition, dépistage, secours, carte).

## 8. Application mobile & mode hors-ligne (PWA)

- Le site est une application web progressive : elle s'installe sur l'écran d'accueil (Android : menu « Installer » ; iPhone : Partager → « Sur l'écran d'accueil »).
- Une fois installée, tous les outils (vaccination, nutrition, dépistage, premiers secours, carte) restent consultables sans réseau grâce au cache hors-ligne. Le triage IA nécessite une connexion.

## 9. Cadre légal et données personnelles

- Politique de confidentialité : {base}/politique-de-confidentialite/ — données collectées (téléphone, profils enfants, mesures), finalités, durée de conservation, droits d'accès, rectification, effacement et opposition. Cadre : loi n° 2017-20 du 20 avril 2018 portant Code du numérique en République du Bénin ; autorité de contrôle : APDP (Autorité de Protection des Données à caractère Personnel).
- Politique des cookies : {base}/politique-des-cookies/ — cookies techniques uniquement (session, sécurité), aucun cookie publicitaire ni traceur tiers ; bandeau d'information non bloquant.
- Conditions d'utilisation : {base}/cgu/.

## 10. À propos

Page : {base}/a-propos/

Santé Infantile Bénin est développé par SOSSA Gninazé Mingnissê Darius, infirmier diplômé d'État et développeur, avec l'ambition de rendre l'information de santé infantile accessible à tous les parents béninois, en français simple, gratuitement, même avec une connexion limitée.
"""
