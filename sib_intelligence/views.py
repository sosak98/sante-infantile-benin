import os
import json
from datetime import date
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from groq import Groq
from accounts.models import Parent
from enfants.models import Enfant

from types import SimpleNamespace

# Initialisation du client Groq (optionnelle : l'IA est désactivée si la clé est absente)
GROQ_API_KEY = os.getenv('GROQ_API_KEY') or getattr(settings, 'GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL') or getattr(settings, 'GROQ_MODEL', 'openai/gpt-oss-20b')
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


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
    """Construit le prompt système sécurisé pour l'IA"""

    system_prompt = f"""Tu es SIB Intelligence, un assistant médical pédiatrique virtuel de la plateforme Santé Infantile Bénin.

Tu aides les parents béninois à mieux comprendre l'état de santé de leurs enfants.

Contexte de l'enfant :
- Prénom : {enfant_nom}
- Âge : {age_mois} mois
- Résultat du triage : {message}
- Symptômes détectés :
  * Fièvre : {symptomes.get('fievre', 'Non renseigné')}
  * Diarrhée : {symptomes.get('diarrhee', 'Non renseigné')}
  * Respiration : {symptomes.get('respiration', 'Non renseigné')}
  * Éveil : {symptomes.get('eveil', 'Non renseigné')}
  * Alimentation : {symptomes.get('alimentation', 'Non renseigné')}
  * Convulsions : {symptomes.get('convulsions', 'Non renseigné')}
  * Vomissements : {symptomes.get('vomissement', 'Non renseigné')}
  * Poids : {symptomes.get('poids', 'Non renseigné')} kg
  * Taille : {symptomes.get('taille', 'Non renseigné')} cm
  * MUAC : {symptomes.get('muac', 'Non renseigné')} cm

Règles importantes :
1. Réponds TOUJOURS en français
2. Sois rassurant mais honnête
3. Si urgence rouge ou jaune, recommande toujours de consulter un médecin
4. Donne des conseils pratiques adaptés au contexte béninois
5. Ne pose pas de diagnostic médical définitif
6. Reste simple et compréhensible pour des parents non-médecins
7. Réponds en phrases courtes et COMPLÈTES. Pas de markdown : pas d'astérisques, pas de dièses, pas de tableaux.
8. Si tu listes, utilise des tirets simples et une ligne par idée.
9. Si convulsions, insiste fortement sur l'urgence (112).
10. Si MUAC ou IMC indique une malnutrition, donne des conseils nutritionnels adaptés."""

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
            'contexte': json.dumps(contexte),
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
