import os
import json
from datetime import date
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from groq import Groq
from accounts.models import Parent
from enfants.models import Enfant

# Initialisation du client Groq (optionnelle : l'IA est désactivée si la clé est absente)
GROQ_API_KEY = os.getenv('GROQ_API_KEY') or getattr(settings, 'GROQ_API_KEY', '')
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
        return 'rouge', '🔴 Urgence immédiate — Consultez un médecin maintenant !', score
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
7. Limite tes réponses à 150 mots maximum
8. Si convulsions, insiste fortement sur l'urgence
9. Si MUAC ou IMC indique une malnutrition, donne des conseils nutritionnels adaptés"""

    return system_prompt


@login_required
def triage(request):
    parent, _ = Parent.objects.get_or_create(user=request.user)
    enfants = Enfant.objects.filter(parent=parent)

    if request.method == 'POST':
        enfant_id = request.POST.get('enfant_id')

        # Sécurité : vérifier que l'enfant appartient bien au parent
        enfant = get_object_or_404(Enfant, id=enfant_id, parent=parent)

        # Récupération des symptômes
        symptomes = {
            'fievre': request.POST.get('fievre'),
            'diarrhee': request.POST.get('diarrhee'),
            'respiration': request.POST.get('respiration'),
            'eveil': request.POST.get('eveil'),
            'alimentation': request.POST.get('alimentation'),
            'convulsions': request.POST.get('convulsions'),
            'vomissement': request.POST.get('vomissement'),
            'poids': request.POST.get('poids'),
            'taille': request.POST.get('taille'),
            'muac': request.POST.get('muac'),
        }

        poids = symptomes.get('poids')
        taille = symptomes.get('taille')
        muac = symptomes.get('muac')

        # Calcul de l'âge en mois
        today = date.today()
        age_mois = (today.year - enfant.date_naissance.year) * 12 + (today.month - enfant.date_naissance.month)

        # Calcul du score et classification
        niveau, message, score = calculer_score_triage(symptomes, poids, taille, muac)

        # Contexte pour le chat
        contexte = {
            'enfant_nom': enfant.prenom,
            'age_mois': age_mois,
            'niveau': niveau,
            'message': message,
            'symptomes': {
                'fievre': symptomes.get('fievre', 'Non renseigné'),
                'diarrhee': symptomes.get('diarrhee', 'Non renseigné'),
                'respiration': symptomes.get('respiration', 'Non renseigné'),
                'eveil': symptomes.get('eveil', 'Non renseigné'),
                'alimentation': symptomes.get('alimentation', 'Non renseigné'),
                'convulsions': symptomes.get('convulsions', 'Non renseigné'),
                'vomissement': symptomes.get('vomissement', 'Non renseigné'),
                'poids': poids if poids else 'Non renseigné',
                'taille': taille if taille else 'Non renseigné',
                'muac': muac if muac else 'Non renseigné',
            }
        }

        return render(request, 'sib_intelligence/resultat.html', {
            'enfant': enfant,
            'niveau': niveau,
            'message': message,
            'score': score,
            'contexte': json.dumps(contexte),
            'enfants': enfants,
            'age_mois': age_mois,
        })

    return render(request, 'sib_intelligence/triage.html', {
        'enfants': enfants,
        'parent': parent,
    })


@login_required
@csrf_exempt
def chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_user = data.get('message', '')
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
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message_user}
                ],
                max_tokens=300,
                temperature=0.7,
            )
            reponse = completion.choices[0].message.content

            # Informations utiles pour le front-end
            niveau = contexte.get('niveau', 'vert')
            suggestion = 'hospital' if niveau == 'rouge' else ('clinic' if niveau == 'jaune' else 'home')

            return JsonResponse({
                'reponse': reponse,
                'status': 'ok',
                'suggestion': suggestion,
                'message_bref': contexte.get('message', '').split('—')[0] if contexte.get('message') else ''
            })

        except json.JSONDecodeError:
            return JsonResponse({'reponse': 'Format de message invalide', 'status': 'error'}, status=400)
        except Exception as e:
            return JsonResponse({'reponse': 'Erreur technique. Veuillez réessayer.', 'status': 'error'}, status=500)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
