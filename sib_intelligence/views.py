import os
import json
from datetime import date
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from accounts.models import Parent
from enfants.models import Enfant

from types import SimpleNamespace

# Poids pour la taille selon les standards OMS (tables LMS embarquées dans
# enfants/data/oms). Import tolérant : si les tables venaient à manquer, le
# triage continue de fonctionner et l'indicateur est simplement ignoré.
try:
    from enfants.oms_lms import z_poids_taille
except Exception:  # tables absentes : l'indicateur est simplement ignoré
    z_poids_taille = None

# Initialisation du client Groq (optionnelle : l'IA est désactivée si la clé est absente)
GROQ_API_KEY = os.getenv('GROQ_API_KEY') or getattr(settings, 'GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL') or getattr(settings, 'GROQ_MODEL', 'openai/gpt-oss-20b')


def _client_groq():
    """Client Groq, construit à la demande.

    L'import était fait au chargement du module : si le paquet `groq` manquait
    (ou cassait), TOUT le site tombait en erreur 500, y compris la vaccination
    et les premiers secours, alors que l'IA n'est qu'un module secondaire.
    Ici, l'absence de la librairie ou de la clé désactive seulement le chat.
    """
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
    except Exception:  # librairie absente ou incompatible
        return None
    try:
        return Groq(api_key=GROQ_API_KEY)
    except Exception:
        return None


def z_poids_pour_taille(symptomes, age_mois=None):
    """Écart-type du poids pour la taille, selon les standards OMS.

    L'ancienne version calculait un IMC et le comparait à 14 et 16. Un IMC
    brut n'a pas de sens avant cinq ans : il culmine vers 6 à 9 mois puis
    décroît, si bien qu'un seuil fixe classe mal à tous les âges. L'OMS
    retient le poids pour la taille exprimé en écarts-types, par sexe.

    Retourne None quand l'indicateur ne peut pas être calculé correctement
    (sexe, poids, taille ou âge absent, âge hors de la fenêtre de 0 à
    59 mois, tables OMS indisponibles) : il est alors ignoré silencieusement
    plutôt que mal calculé.

    Source : OMS, standards de croissance de l'enfant, tables LMS
    poids pour la taille (enfants/oms_lms.py).
    """
    if z_poids_taille is None or age_mois is None:
        return None
    # Le poids pour la taille est la référence OMS des enfants de moins de
    # cinq ans. Au-delà, la référence devient l'IMC pour l'âge (5 à 19 ans),
    # que ce module ne calcule pas : l'indicateur est ignoré silencieusement,
    # comme le périmètre brachial hors de sa fenêtre de 6 à 59 mois. Les
    # tables embarquées montent pourtant jusqu'à 120 cm, d'où cette borne
    # explicite, qui évite de lire un enfant de 6 à 10 ans sur la courbe des
    # moins de cinq ans.
    try:
        if not 0 <= int(age_mois) <= 59:
            return None
    except (TypeError, ValueError):
        return None
    sexe = symptomes.get('sexe')
    poids = symptomes.get('poids')
    taille = symptomes.get('taille')
    if not (sexe and poids and taille):
        return None
    try:
        return z_poids_taille(float(poids), float(taille), sexe, int(age_mois))
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def reperer_signes_danger(symptomes, muac=None, age_mois=None):
    """Signes généraux de danger de la PCIME.

    Un seul de ces signes impose une prise en charge immédiate, quel que
    soit le reste du tableau clinique. Ils ne peuvent donc pas être traités
    comme des points qui s'additionnent : une convulsion isolée pesait
    4 points sur un seuil de 6 et ressortait en consultation sous 48 heures.
    Ils court-circuitent maintenant le score.

    Sources :
    - PCIME Bénin, OMS, signes généraux de danger :
      https://platform.who.int/docs/default-source/mca-documents/policy-documents/operational-guidance/ben-mn-62-01-operationalguidance-fra-imnci-booklet.pdf
    - OMS et UNICEF, 2009, identification de la malnutrition aiguë sévère,
      seuil du périmètre brachial porté à 115 mm pour les 6 à 59 mois :
      https://www.who.int/publications/i/item/9789241598163
    - OMS, malnutrition aiguë sévère avant 6 mois, définie par le poids pour
      la taille sous moins trois écarts-types ou des œdèmes bilatéraux :
      https://www.who.int/tools/elena/interventions/sam-identification-infants
    """
    signes = []
    if symptomes.get('convulsions') == 'oui':
        signes.append('convulsions pendant la maladie actuelle')
    if symptomes.get('eveil') in ('difficile', 'non'):
        signes.append('enfant léthargique ou inconscient')
    if symptomes.get('alimentation') == 'refuse':
        signes.append('incapable de boire ou de prendre le sein')
    if symptomes.get('vomissement') == 'oui_tout':
        signes.append('vomit tout ce qu\u2019il consomme')
    if symptomes.get('respiration') == 'difficile':
        signes.append('difficulté respiratoire')
    # Le périmètre brachial n'est interprétable qu'entre 6 et 59 mois.
    if muac and str(muac).strip() and (age_mois is None or 6 <= age_mois <= 59):
        try:
            if float(muac) < 11.5:
                signes.append('périmètre brachial inférieur à 11,5 cm')
        except (TypeError, ValueError):
            pass
    z = z_poids_pour_taille(symptomes, age_mois)
    if z is not None and z < -3:
        signes.append('poids pour la taille inférieur à moins trois '
                      'écarts-types, malnutrition aiguë sévère')
    return signes


def reperer_motifs_consultation(symptomes, muac=None, age_mois=None):
    """Situations qui imposent au minimum une consultation.

    Elles ne sont pas des urgences vitales, mais elles ne peuvent pas non
    plus se résoudre par des conseils à domicile. Sans cette liste, une
    malnutrition aiguë modérée isolée valait 2 points sur un seuil de 3 et
    ressortait en vert.

    Sources : OMS et UNICEF, 2009, seuils du périmètre brachial (115 à
    125 mm) et du poids pour la taille (moins deux à moins trois
    écarts-types) pour la malnutrition aiguë modérée, entre 6 et 59 mois.
    """
    motifs = []
    if muac and str(muac).strip() and (age_mois is None or 6 <= age_mois <= 59):
        try:
            valeur = float(muac)
            if 11.5 <= valeur < 12.5:
                motifs.append('périmètre brachial entre 11,5 et 12,5 cm, '
                              'malnutrition aiguë modérée')
        except (TypeError, ValueError):
            pass
    z = z_poids_pour_taille(symptomes, age_mois)
    if z is not None and -3 <= z < -2:
        motifs.append('poids pour la taille entre moins deux et moins trois '
                      'écarts-types, malnutrition aiguë modérée')
    return motifs


def calculer_score_triage(symptomes, poids=None, taille=None, muac=None, age_mois=None):
    """Calcule le score de gravité et retourne (niveau, message, score, signes).

    Les signes généraux de danger de la PCIME ne sont plus des points qui
    s'additionnent : un seul d'entre eux impose une prise en charge
    immédiate et court-circuite le score. Le score ne porte donc plus que
    sur les symptômes gradués qui ne figurent pas dans cette liste, et le
    bloc IMC a été retiré au profit du poids pour la taille en écarts-types.
    """
    score = 0

    # Fièvre
    fievre = symptomes.get('fievre')
    if fievre == 'oui_haute':
        score += 3
    elif fievre == 'oui_moderee':
        score += 1

    # Diarrhée
    diarrhee = symptomes.get('diarrhee')
    if diarrhee == 'oui_sang':
        score += 3
    elif diarrhee == 'oui_simple':
        score += 1

    # Respiration. La respiration difficile, le tirage et le geignement sont
    # un signe général de danger traité à part : seule la respiration rapide
    # compte ici.
    if symptomes.get('respiration') == 'rapide':
        score += 2

    # Alimentation. L'incapacité de boire ou de prendre le sein est un signe
    # général de danger traité à part : seule la diminution compte ici.
    if symptomes.get('alimentation') == 'diminuee':
        score += 1

    # Vomissements. "Vomit tout ce qu'il consomme" est un signe général de
    # danger traité à part. Des vomissements répétés qui gardent des liquides
    # n'en sont pas un : la PCIME distingue explicitement les deux.
    vomissement = symptomes.get('vomissement')
    if vomissement == 'oui_repete':
        score += 2
    elif vomissement == 'oui_simple':
        score += 1

    # Classification. Un signe général de danger prime sur le score.
    signes = reperer_signes_danger(symptomes, muac, age_mois)
    if signes:
        return ('rouge', 'Urgence immédiate : rendez-vous au centre de santé '
                'le plus proche maintenant.', score, signes)
    if score >= 6:
        return ('rouge', 'Urgence immédiate : rendez-vous au centre de santé '
                'le plus proche maintenant.', score, signes)
    if score >= 3 or reperer_motifs_consultation(symptomes, muac, age_mois):
        return 'jaune', 'Consultation recommandée dans les 24-48h', score, signes
    return 'vert', 'Conseils à domicile suffisants pour le moment', score, signes


def construire_contexte_systeme(enfant_nom, age_mois, niveau, message, symptomes,
                                signes_danger=None):
    """Construit le prompt système sécurisé pour l'IA selon le niveau de gravité du triage.

    `signes_danger` porte les signes généraux de danger relevés par le triage.
    Ils sont transmis à l'assistant avec la consigne de les nommer au parent
    en mots simples : ce sont eux qui motivent l'orientation, le parent doit
    pouvoir les reconnaître et les redire à l'agent de santé.
    """

    if signes_danger:
        liste_signes = '\n'.join('  - ' + signe for signe in signes_danger)
        bloc_signes = (
            "- Signes généraux de danger relevés :\n"
            f"{liste_signes}\n"
            "  Un seul de ces signes suffit à imposer une prise en charge "
            "immédiate, quels que soient les autres symptômes.\n"
            "  CONSIGNE : nomme chacun de ces signes au parent en mots simples, "
            "sans jargon médical, et explique pourquoi il impose de se rendre "
            "immédiatement au centre de santé le plus proche."
        )
    else:
        bloc_signes = "- Signes généraux de danger relevés : aucun"

    # L'âge peut manquer (triage sans dossier, champ vide) : on l'écrit alors
    # en toutes lettres plutôt que "None mois" dans le prompt.
    age_libelle = (f'{age_mois} mois'
                   if isinstance(age_mois, (int, float)) else str(age_mois))

    if niveau == 'rouge':
        consignes_specifiques = """RÈGLES STRICTES D'URGENCE MÉDICALE (NIVEAU ROUGE) :
1. TON ET OBJECTIF : Message ferme, clair et direct. C'est une urgence vitale. L'enfant doit être examiné par un médecin immédiatement.
2. MESSAGE PRINCIPAL FERME : Rappelle dès le début de se rendre immédiatement au centre de santé le plus proche ou d'appeler le 112.
3. GESTES DE PREMIERS SECOURS MINIMAUX ET SÛRS UNIQUEMENT (en attendant les soins) :
   - Garder son calme et rassurer l'enfant.
   - Si l'enfant est inconscient mais respire : le placer en position latérale de sécurité (PLS).
   - Si convulsions ou perte de conscience : ne RIEN donner par la bouche (ni eau, ni aliment, ni médicament - risque mortel d'étouffement), ne pas bloquer les mouvements.
   - Surveiller continuellement la respiration de l'enfant.
   - Ne jamais secouer un bébé ou un jeune enfant.
   - Consulter la carte des centres de santé sur le site SIB pour trouver le centre le plus proche.
4. INTERDICTIONS FORMELLES ET ABSOLUES EN MODE ROUGE :
   - INTERDICTION de prescrire ou de mentionner la moindre posologie de médicament (aucun dosage de zinc, aucun dosage de paracétamol, etc.).
   - INTERDICTION de donner un protocole de soins multi-jours (aucun traitement sur 10 jours, etc.) qui donnerait l'illusion dangereuse de pouvoir soigner l'enfant à la maison.
   - Ne donne AUCUNE instruction qui risquerait de retarder la consultation médicale immédiate."""
    elif niveau == 'jaune':
        consignes_specifiques = """RÈGLES POUR CONSULTATION RECOMMANDÉE (NIVEAU JAUNE) :
1. Rappelle que l'enfant doit être vu par un professionnel de santé dans les 24 à 48 heures.
2. Conseils simples en attendant la consultation : hydratation régulière (continuer l'allaitement maternel, solution de réhydratation orale), alimentation légère, repos.
3. RÈGLE MÉDICAMENTS ET ZINC : Ne mentionne AUCUN chiffre ni dosage de médicament ou de zinc. Dis clairement : 'Demandez à un agent de santé le dosage adapté à votre enfant'.
4. Indique les signes d'aggravation qui imposent de passer immédiatement aux urgences (112)."""
    else:
        consignes_specifiques = """RÈGLES POUR SUIVI À DOMICILE (NIVEAU VERT) :
1. Rassure le parent tout en encourageant la vigilance habituelle.
2. Conseils pratiques de puériculture adaptés au Bénin : hydratation, maintien de l'allaitement maternel, alimentation variée selon l'âge.
3. RÈGLE MÉDICAMENTS : Ne donne AUCUNE posologie précise de médicament. Pour tout traitement ou complément, renvoie vers un professionnel de santé.
4. Précise les signes qui doivent motiver une consultation si l'état de l'enfant venait à changer."""

    system_prompt = f"""Tu es SIB Intelligence, l'assistant médical pédiatrique de la plateforme Santé Infantile Bénin.
Tu aides les parents béninois à comprendre les résultats du triage et à adopter les bons réflexes pour leur enfant.

Contexte de l'enfant :
- Prénom : {enfant_nom}
- Âge : {age_libelle}
- Niveau de gravité : {niveau.upper()}
- Message du triage : {message}
{bloc_signes}
- Symptômes observés :
  * Fièvre : {symptomes.get('fievre', 'Non renseigné')}
  * Diarrhée : {symptomes.get('diarrhee', 'Non renseigné')}
  * Respiration : {symptomes.get('respiration', 'Non renseigné')}
  * Éveil : {symptomes.get('eveil', 'Non renseigné')}
  * Alimentation : {symptomes.get('alimentation', 'Non renseigné')}
  * Convulsions : {symptomes.get('convulsions', 'Non renseigné')}
  * Vomissements : {symptomes.get('vomissement', 'Non renseigné')}
  * Sexe : {symptomes.get('sexe', 'Non renseigné')}
  * Poids : {symptomes.get('poids', 'Non renseigné')} kg
  * Taille : {symptomes.get('taille', 'Non renseigné')} cm
  * Périmètre brachial : {symptomes.get('muac', 'Non renseigné')} cm

{consignes_specifiques}

Règles de style et de formulation :
1. Réponds TOUJOURS en français simple et bienveillant.
2. Structure tes réponses en paragraphes courts et utilise des tirets simples (-) pour les listes.
3. N'utilise aucun tiret cadratin dans tes réponses.
4. Ne pose pas de diagnostic médical définitif : tu es un outil d'orientation et de premiers secours."""

    return system_prompt


def _symptomes_from_post(post):
    return {
        'fievre': post.get('fievre'),
        'diarrhee': post.get('diarrhee'),
        'respiration': post.get('respiration'),
        'eveil': post.get('eveil'),
        'alimentation': post.get('alimentation'),
        'convulsions': post.get('convulsions'),
        'vomissement': post.get('vomissement'),
        'sexe': post.get('sexe'),
        'poids': post.get('poids'),
        'taille': post.get('taille'),
        'muac': post.get('muac'),
    }


@ensure_csrf_cookie
def triage(request):
    parent = None
    enfants = Enfant.objects.none()
    if request.user.is_authenticated:
        parent, _ = Parent.objects.get_or_create(user=request.user)
        enfants = Enfant.objects.filter(parent=parent)

    if request.method == 'POST':
        enfant_id = request.POST.get('enfant_id')
        enfant = None
        if enfant_id and request.user.is_authenticated and parent:
            enfant = get_object_or_404(Enfant, id=enfant_id, parent=parent)
            today = date.today()
            age_mois = (today.year - enfant.date_naissance.year) * 12 + (
                today.month - enfant.date_naissance.month
            )
            prenom = enfant.prenom
        else:
            prenom = (request.POST.get('prenom') or 'votre enfant').strip()
            # Un âge absent ou illisible reste None : le périmètre brachial et
            # le poids pour la taille sont alors ignorés plutôt que calculés
            # sur un âge faux.
            age_brut = (request.POST.get('age_mois') or '').strip()
            try:
                age_mois = int(age_brut)
            except ValueError:
                age_mois = None
            enfant = SimpleNamespace(prenom=prenom)

        symptomes = _symptomes_from_post(request.POST)
        poids = symptomes.get('poids')
        taille = symptomes.get('taille')
        muac = symptomes.get('muac')
        niveau, message, score, signes = calculer_score_triage(
            symptomes, poids, taille, muac, age_mois
        )

        contexte = {
            'enfant_nom': prenom,
            'age_mois': age_mois if age_mois is not None else 'non précisé',
            'niveau': niveau,
            'message': message,
            'invite': not request.user.is_authenticated,
            'signes_danger': signes,
            'symptomes': {
                'fievre': symptomes.get('fievre') or 'Non renseigné',
                'diarrhee': symptomes.get('diarrhee') or 'Non renseigné',
                'respiration': symptomes.get('respiration') or 'Non renseigné',
                'eveil': symptomes.get('eveil') or 'Non renseigné',
                'alimentation': symptomes.get('alimentation') or 'Non renseigné',
                'convulsions': symptomes.get('convulsions') or 'Non renseigné',
                'vomissement': symptomes.get('vomissement') or 'Non renseigné',
                'sexe': symptomes.get('sexe') or 'Non renseigné',
                'poids': poids or 'Non renseigné',
                'taille': taille or 'Non renseigné',
                'muac': muac or 'Non renseigné',
            },
        }

        return render(request, 'sib_intelligence/resultat.html', {
            'enfant': enfant,
            'niveau': niveau,
            'message': message,
            'score': score,
            'signes': signes,
            'contexte': contexte,
            'enfants': enfants,
            'age_mois': age_mois,
            'invite': not request.user.is_authenticated,
        })

    return render(request, 'sib_intelligence/triage.html', {
        'enfants': enfants,
        'parent': parent,
        'invite': not request.user.is_authenticated,
    })


def chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_user = data.get('message', '')[:1500]
            # Anti-abus : 30 messages / 5 min / IP (le quota Groq coute)
            ip_client = (request.META.get('HTTP_X_FORWARDED_FOR', '')
                         .split(',')[0].strip() or request.META.get('REMOTE_ADDR', ''))
            cle = f"chat_rl:{ip_client}"
            compteur = cache.get(cle, 0)
            if compteur >= 30:
                return JsonResponse({
                    'reponse': "Beaucoup de questions d'affilée. Patientez quelques "
                               "minutes, l'assistant a besoin de souffler.",
                    'status': 'ok',
                }, status=429)
            cache.set(cle, compteur + 1, timeout=300)
            contexte = data.get('contexte', {})
            symptomes = contexte.get('symptomes', {})

            client = _client_groq()
            if client is None:
                return JsonResponse({
                    'reponse': "L'assistant IA est temporairement indisponible (clé API non configurée). "
                               "Veuillez consulter un professionnel de santé pour toute question.",
                    'status': 'ok',
                    'suggestion': contexte.get('niveau', 'vert'),
                })

            system_prompt = construire_contexte_systeme(
                enfant_nom=contexte.get('enfant_nom', 'mon enfant'),
                age_mois=contexte.get('age_mois', '?'),
                niveau=contexte.get('niveau', '?'),
                message=contexte.get('message', ''),
                symptomes=symptomes,
                signes_danger=contexte.get('signes_danger') or [],
            )

            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message_user}
                ],
                max_tokens=700,
                temperature=0.4,
            )
            reponse = completion.choices[0].message.content

            # Informations utiles pour le front-end
            niveau = contexte.get('niveau', 'vert')
            suggestion = 'hospital' if niveau == 'rouge' else ('clinic' if niveau == 'jaune' else 'home')

            return JsonResponse({
                'reponse': reponse,
                'status': 'ok',
                'suggestion': suggestion,
            })

        except json.JSONDecodeError:
            return JsonResponse({'reponse': 'Format de message invalide', 'status': 'error'}, status=400)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception('Erreur chat IA')
            return JsonResponse({
                'reponse': "L'assistant rencontre une difficulté technique. "
                           "Réessayez dans un instant ou adressez-vous à un professionnel de santé.",
                'status': 'error',
            }, status=500)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
