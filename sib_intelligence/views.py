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


def calculer_score_triage(symptomes, poids=None, taille=None, muac=None):
    """Calcule le score de gravité et retourne le niveau (rouge/jaune/vert)"""
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

    # Respiration
    respiration = symptomes.get('respiration')
    if respiration == 'difficile':
        score += 3
    elif respiration == 'rapide':
        score += 2

    # Éveil
    eveil = symptomes.get('eveil')
    if eveil == 'non':
        score += 3
    elif eveil == 'difficile':
        score += 2

    # Alimentation
    alimentation = symptomes.get('alimentation')
    if alimentation == 'refuse':
        score += 3
    elif alimentation == 'diminuee':
        score += 1

    # Convulsions
    if symptomes.get('convulsions') == 'oui':
        score += 4

    # Vomissements
    vomissement = symptomes.get('vomissement')
    if vomissement == 'oui_repete':
        score += 2
    elif vomissement == 'oui_simple':
        score += 1

    # MUAC (malnutrition aiguë)
    if muac and muac.strip():
        try:
            muac_val = float(muac)
            if muac_val < 11.5:
                score += 4
            elif muac_val < 12.5:
                score += 2
        except ValueError:
            pass

    # IMC (malnutrition chronique)
    if poids and taille and poids.strip() and taille.strip():
        try:
            poids_val = float(poids)
            taille_val = float(taille) / 100
            if taille_val > 0:
                imc = poids_val / (taille_val ** 2)
                if imc < 14:
                    score += 3
                elif imc < 16:
                    score += 1
        except (ValueError, ZeroDivisionError):
            pass

    # Classification
    if score >= 6:
        return 'rouge', '🔴 Urgence immédiate : consultez un médecin maintenant !', score
    elif score >= 3:
        return 'jaune', '🟡 Consultation recommandée dans les 24-48h', score
    else:
        return 'vert', '🟢 Conseils à domicile suffisants pour le moment', score


def construire_contexte_systeme(enfant_nom, age_mois, niveau, message, symptomes):
    """Construit le prompt système sécurisé pour l'IA selon le niveau de gravité du triage"""

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
- Âge : {age_mois} mois
- Niveau de gravité : {niveau.upper()}
- Message du triage : {message}
- Symptômes observés :
  * Fièvre : {symptomes.get('fievre', 'Non renseigné')}
  * Diarrhée : {symptomes.get('diarrhee', 'Non renseigné')}
  * Respiration : {symptomes.get('respiration', 'Non renseigné')}
  * Éveil : {symptomes.get('eveil', 'Non renseigné')}
  * Alimentation : {symptomes.get('alimentation', 'Non renseigné')}
  * Convulsions : {symptomes.get('convulsions', 'Non renseigné')}
  * Vomissements : {symptomes.get('vomissement', 'Non renseigné')}
  * Poids : {symptomes.get('poids', 'Non renseigné')} kg
  * Taille : {symptomes.get('taille', 'Non renseigné')} cm
  * MUAC (bras) : {symptomes.get('muac', 'Non renseigné')} cm

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
            try:
                age_mois = int(request.POST.get('age_mois') or 0)
            except ValueError:
                age_mois = 0
            enfant = SimpleNamespace(prenom=prenom)

        symptomes = _symptomes_from_post(request.POST)
        poids = symptomes.get('poids')
        taille = symptomes.get('taille')
        muac = symptomes.get('muac')
        niveau, message, score = calculer_score_triage(symptomes, poids, taille, muac)

        contexte = {
            'enfant_nom': prenom,
            'age_mois': age_mois,
            'niveau': niveau,
            'message': message,
            'invite': not request.user.is_authenticated,
            'symptomes': {
                'fievre': symptomes.get('fievre') or 'Non renseigné',
                'diarrhee': symptomes.get('diarrhee') or 'Non renseigné',
                'respiration': symptomes.get('respiration') or 'Non renseigné',
                'eveil': symptomes.get('eveil') or 'Non renseigné',
                'alimentation': symptomes.get('alimentation') or 'Non renseigné',
                'convulsions': symptomes.get('convulsions') or 'Non renseigné',
                'vomissement': symptomes.get('vomissement') or 'Non renseigné',
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
                symptomes=symptomes
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
