import os
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from groq import Groq
from accounts.models import Parent
from enfants.models import Enfant

client = Groq(api_key=os.getenv('GROQ_API_KEY'))


@login_required
def triage(request):
    parent = Parent.objects.get(user=request.user)
    enfants = Enfant.objects.filter(parent=parent)

    if request.method == 'POST':
        enfant_id = request.POST.get('enfant_id')
        fievre = request.POST.get('fievre')
        diarrhee = request.POST.get('diarrhee')
        respiration = request.POST.get('respiration')
        eveil = request.POST.get('eveil')
        alimentation = request.POST.get('alimentation')
        convulsions = request.POST.get('convulsions')
        vomissement = request.POST.get('vomissement')
        poids = request.POST.get('poids')
        taille = request.POST.get('taille')
        muac = request.POST.get('muac')

        enfant = Enfant.objects.get(id=enfant_id, parent=parent)

        from datetime import date
        today = date.today()
        age_mois = (today.year - enfant.date_naissance.year) * 12 + (today.month - enfant.date_naissance.month)

        # ===== Calcul du score de triage =====
        score = 0
        if fievre == 'oui_haute': score += 3
        elif fievre == 'oui_moderee': score += 1
        if diarrhee == 'oui_sang': score += 3
        elif diarrhee == 'oui_simple': score += 1
        if respiration == 'difficile': score += 3
        elif respiration == 'rapide': score += 2
        if eveil == 'non': score += 3
        elif eveil == 'difficile': score += 2
        if alimentation == 'refuse': score += 3
        elif alimentation == 'diminuee': score += 1
        if convulsions == 'oui': score += 4
        if vomissement == 'oui_repete': score += 2
        elif vomissement == 'oui_simple': score += 1

        # Malnutrition via MUAC
        if muac:
            muac_val = float(muac)
            if muac_val < 11.5: score += 4
            elif muac_val < 12.5: score += 2

        # Malnutrition via IMC
        if poids and taille:
            poids_val = float(poids)
            taille_val = float(taille) / 100
            imc = poids_val / (taille_val ** 2)
            if imc < 14: score += 3
            elif imc < 16: score += 1

        # ===== Classification =====
        if score >= 6:
            niveau = 'rouge'
            message = '🔴 Urgence immédiate — Consultez un médecin maintenant !'
        elif score >= 3:
            niveau = 'jaune'
            message = '🟡 Consultation recommandée dans les 24-48h'
        else:
            niveau = 'vert'
            message = '🟢 Conseils à domicile suffisants pour le moment'

        contexte = {
            'enfant_nom': enfant.prenom,
            'age_mois': age_mois,
            'niveau': niveau,
            'message': message,
            'symptomes': {
                'fievre': fievre,
                'diarrhee': diarrhee,
                'respiration': respiration,
                'eveil': eveil,
                'alimentation': alimentation,
                'convulsions': convulsions,
                'vomissement': vomissement,
                'poids': poids,
                'taille': taille,
                'muac': muac,
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
        data = json.loads(request.body)
        message_user = data.get('message', '')
        contexte = data.get('contexte', {})
        symptomes = contexte.get('symptomes', {})

        system_prompt = f"""Tu es SIB Intelligence, un assistant médical pédiatrique virtuel de la plateforme Santé Infantile Bénin.

Tu aides les parents béninois à mieux comprendre l'état de santé de leurs enfants.

Contexte de l'enfant :
- Prénom : {contexte.get('enfant_nom', 'N/A')}
- Âge : {contexte.get('age_mois', 'N/A')} mois
- Résultat du triage : {contexte.get('message', 'N/A')}
- Symptômes détectés :
  * Fièvre : {symptomes.get('fievre', 'N/A')}
  * Diarrhée : {symptomes.get('diarrhee', 'N/A')}
  * Respiration : {symptomes.get('respiration', 'N/A')}
  * Éveil : {symptomes.get('eveil', 'N/A')}
  * Alimentation : {symptomes.get('alimentation', 'N/A')}
  * Convulsions : {symptomes.get('convulsions', 'N/A')}
  * Vomissements : {symptomes.get('vomissement', 'N/A')}
  * Poids : {symptomes.get('poids', 'N/A')} kg
  * Taille : {symptomes.get('taille', 'N/A')} cm
  * MUAC : {symptomes.get('muac', 'N/A')} cm

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

        try:
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
            return JsonResponse({'reponse': reponse, 'status': 'ok'})

        except Exception as e:
            return JsonResponse({'reponse': f'Erreur : {str(e)}', 'status': 'error'})

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
