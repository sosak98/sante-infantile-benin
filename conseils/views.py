from django.shortcuts import render
from django.http import JsonResponse
from datetime import date, timedelta
from .models import Vaccin, ConseilNutritionnel

def calendrier_vaccinal(request):
    vaccins = Vaccin.objects.all()
    return render(request, 'conseils/calendrier.html', {'vaccins': vaccins})

def conseils_nutritionnels(request):
    conseils = None
    age_mois = None
    categorie = None

    if request.method == 'POST':
        age_mois = int(request.POST.get('age_mois'))
        categorie = request.POST.get('categorie')
        conseils = ConseilNutritionnel.objects.filter(
            age_min_mois__lte=age_mois,
            age_max_mois__gte=age_mois
        )
        if categorie != 'tous':
            conseils = conseils.filter(categorie=categorie)

    return render(request, 'conseils/nutrition.html', {
        'conseils': conseils,
        'age_mois': age_mois,
        'categorie': categorie,
    })

def calculer_rdv(request):
    resultats = None
    if request.method == 'POST':
        date_naissance_str = request.POST.get('date_naissance')
        date_naissance = date.fromisoformat(date_naissance_str)
        aujourd_hui = date.today()

        # Vaccins reçus
        vaccins_recus = {}
        noms_vaccins = request.POST.getlist('nom_vaccin[]')
        dates_vaccins = request.POST.getlist('date_vaccin[]')
        for nom, d in zip(noms_vaccins, dates_vaccins):
            if nom and d:
                vaccins_recus[nom] = date.fromisoformat(d)

        # Définition des vaccins
        VACCINS_AGE_FIXE = [
            {'nom': 'BCG', 'dose': '1', 'semaines': 0},
            {'nom': 'VPO 0', 'dose': '1', 'semaines': 0},
            {'nom': 'Hépatite B', 'dose': '1', 'semaines': 0},
            {'nom': 'VAR', 'dose': '1', 'semaines': 39},
            {'nom': 'VAA', 'dose': '1', 'semaines': 39},
            {'nom': 'MenA', 'dose': '1', 'semaines': 39},
        ]

        VACCINS_SERIE = [
            # Pentavalent
            {'nom': 'Pentavalent', 'dose': '1', 'semaines_min': 6, 'precedent': None},
            {'nom': 'Pentavalent', 'dose': '2', 'semaines_min': 10, 'precedent': 'Pentavalent_1'},
            {'nom': 'Pentavalent', 'dose': '3', 'semaines_min': 14, 'precedent': 'Pentavalent_2'},
            # VPO
            {'nom': 'VPO', 'dose': '1', 'semaines_min': 6, 'precedent': None},
            {'nom': 'VPO', 'dose': '2', 'semaines_min': 10, 'precedent': 'VPO_1'},
            {'nom': 'VPO',
