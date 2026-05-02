from django.shortcuts import render
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
        vaccins_recus = {}
        noms_vaccins = request.POST.getlist('nom_vaccin[]')
        dates_vaccins = request.POST.getlist('date_vaccin[]')
        for nom, d in zip(noms_vaccins, dates_vaccins):
            if nom and d:
                vaccins_recus[nom] = date.fromisoformat(d)
        VACCINS_AGE_FIXE = [
            {'nom': 'BCG', 'dose': '1', 'semaines': 0},
            {'nom': 'VPO 0', 'dose': '1', 'semaines': 0},
            {'nom': 'Hepatite B', 'dose': '1', 'semaines': 0},
            {'nom': 'VAR', 'dose': '1', 'semaines': 39},
            {'nom': 'VAA', 'dose': '1', 'semaines': 39},
            {'nom': 'MenA', 'dose': '1', 'semaines': 39},
        ]
        VACCINS_SERIE = [
            {'nom': 'Pentavalent', 'dose': '1', 'semaines_min': 6, 'precedent': None},
            {'nom': 'Pentavalent', 'dose': '2', 'semaines_min': 10, 'precedent': 'Pentavalent_1'},
            {'nom': 'Pentavalent', 'dose': '3', 'semaines_min': 14, 'precedent': 'Pentavalent_2'},
            {'nom': 'VPO', 'dose': '1', 'semaines_min': 6, 'precedent': None},
            {'nom': 'VPO', 'dose': '2', 'semaines_min': 10, 'precedent': 'VPO_1'},
            {'nom': 'VPO', 'dose': '3', 'semaines_min': 14, 'precedent': 'VPO_2'},
            {'nom': 'PCV', 'dose': '1', 'semaines_min': 6, 'precedent': None},
            {'nom': 'PCV', 'dose': '2', 'semaines_min': 10, 'precedent': 'PCV_1'},
            {'nom': 'PCV', 'dose': '3', 'semaines_min': 14, 'precedent': 'PCV_2'},
            {'nom': 'RTSS', 'dose': '1', 'semaines_min': 22, 'precedent': None},
            {'nom': 'RTSS', 'dose': '2', 'semaines_min': 26, 'precedent': 'RTSS_1'},
            {'nom': 'RTSS', 'dose': '3', 'semaines_min': 39, 'precedent': 'RTSS_2'},
            {'nom': 'RTSS', 'dose': '4', 'semaines_min': 65, 'precedent': 'RTSS_3'},
        ]
        resultats = []
        for v in VACCINS_AGE_FIXE:
            cle = v['nom']
            date_age_min = date_naissance + timedelta(weeks=v['semaines'])
            if cle in vaccins_recus:
                statut = 'Recu'
                date_prevue = vaccins_recus[cle]
                couleur = 'success'
            else:
                date_prevue = date_age_min
                if aujourd_hui < date_prevue:
                    statut = 'A venir'
                    couleur = 'info'
                elif aujourd_hui == date_prevue:
                    statut = 'Aujourd_hui'
                    couleur = 'warning'
                else:
                    statut = 'En retard'
                    couleur = 'danger'
            resultats.append({
                'nom': v['nom'],
                'dose': v['dose'],
                'date_prevue': date_prevue,
                'statut': statut,
                'couleur': couleur,
            })
        dates_doses = {}
        for v in VACCINS_SERIE:
            cle = v['nom'] + '_' + v['dose']
            date_age_min = date_naissance + timedelta(weeks=v['semaines_min'])
            if v['precedent'] and v['precedent'] in dates_doses:
                date_intervalle = dates_doses[v['precedent']] + timedelta(weeks=4)
            else:
                date_intervalle = None
            if date_intervalle:
                date_finale = max(date_age_min, date_intervalle)
            else:
                date_finale = date_age_min
            if cle in vaccins_recus:
                statut = 'Recu'
                date_finale = vaccins_recus[cle]
                couleur = 'success'
                dates_doses[cle] = date_finale
            else:
                dates_doses[cle] = date_finale
                if aujourd_hui < date_finale:
                    statut = 'A venir'
                    couleur = 'info'
                elif aujourd_hui == date_finale:
                    statut = 'Aujourd_hui'
                    couleur = 'warning'
                else:
                    statut = 'En retard'
                    couleur = 'danger'
            resultats.append({
                'nom': v['nom'] + ' dose ' + v['dose'],
                'dose': v['dose'],
                'date_prevue': date_finale,
                'statut': statut,
                'couleur': couleur,
            })
        resultats.sort(key=lambda x: x['date_prevue'])
    return render(request, 'conseils/rdv.html', {'resultats': resultats})
