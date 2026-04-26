from django.shortcuts import render
from datetime import date

def calculer_age_mois(date_naissance):
    aujourd_hui = date.today()
    mois = (aujourd_hui.year - date_naissance.year) * 12 + (aujourd_hui.month - date_naissance.month)
    return mois

def evaluer_malnutrition(poids, taille, age_mois, sexe, muac=None):
    resultats = []

    # --- Poids pour l'âge (simplifié OMS) ---
    # Médiane approximative OMS garçon/fille
    if sexe == 'M':
        mediane_poids = 3.3 + (age_mois * 0.45) if age_mois <= 12 else 9.6 + ((age_mois - 12) * 0.2)
    else:
        mediane_poids = 3.2 + (age_mois * 0.42) if age_mois <= 12 else 9.0 + ((age_mois - 12) * 0.18)

    ecart_type_poids = mediane_poids * 0.12
    zscore_poids = (poids - mediane_poids) / ecart_type_poids

    if zscore_poids < -3:
        resultats.append({"indicateur": "Poids pour l'âge", "statut": "Malnutrition sévère", "couleur": "danger"})
    elif zscore_poids < -2:
        resultats.append({"indicateur": "Poids pour l'âge", "statut": "Malnutrition modérée", "couleur": "warning"})
    elif zscore_poids < -1:
        resultats.append({"indicateur": "Poids pour l'âge", "statut": "Risque de malnutrition", "couleur": "info"})
    else:
        resultats.append({"indicateur": "Poids pour l'âge", "statut": "Normal ✅", "couleur": "success"})

    # --- IMC ---
    taille_m = taille / 100
    imc = poids / (taille_m ** 2)

    if imc < 16:
        resultats.append({"indicateur": "IMC", "statut": "Malnutrition sévère", "couleur": "danger"})
    elif imc < 17:
        resultats.append({"indicateur": "IMC", "statut": "Malnutrition modérée", "couleur": "warning"})
    elif imc < 18.5:
        resultats.append({"indicateur": "IMC", "statut": "Risque de malnutrition", "couleur": "info"})
    else:
        resultats.append({"indicateur": "IMC", "statut": "Normal ✅", "couleur": "success"})

    # --- MUAC ---
    if muac:
        if muac < 11.5:
            resultats.append({"indicateur": "MUAC (Périmètre brachial)", "statut": "Malnutrition sévère 🔴", "couleur": "danger"})
        elif muac < 12.5:
            resultats.append({"indicateur": "MUAC (Périmètre brachial)", "statut": "Malnutrition modérée 🟠", "couleur": "warning"})
        else:
            resultats.append({"indicateur": "MUAC (Périmètre brachial)", "statut": "Normal ✅", "couleur": "success"})

    return resultats

def detection_malnutrition(request):
    resultats = None
    if request.method == 'POST':
        try:
            prenom = request.POST.get('prenom')
            sexe = request.POST.get('sexe')
            age_mois = int(request.POST.get('age_mois'))
            poids = float(request.POST.get('poids'))
            taille = float(request.POST.get('taille'))
            muac_val = request.POST.get('muac')
            muac = float(muac_val) if muac_val else None

            resultats = {
                'prenom': prenom,
                'age_mois': age_mois,
                'poids': poids,
                'taille': taille,
                'muac': muac,
                'evaluations': evaluer_malnutrition(poids, taille, age_mois, sexe, muac)
            }
        except Exception as e:
            resultats = {'erreur': str(e)}

    return render(request, 'enfants/malnutrition.html', {'resultats': resultats})
