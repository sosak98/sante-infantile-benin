"""Calendrier PEV Bénin — calcul partagé (RDV + tableau de bord)."""
from datetime import date, timedelta


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


def planifier(date_naissance, vaccins_recus, aujourd_hui=None):
    """vaccins_recus: dict nom -> date. Retourne une liste de dicts."""
    aujourd_hui = aujourd_hui or date.today()
    resultats = []
    for v in VACCINS_AGE_FIXE:
        cle = v['nom']
        date_age_min = date_naissance + timedelta(weeks=v['semaines'])
        if cle in vaccins_recus:
            statut, date_prevue, couleur = 'Recu', vaccins_recus[cle], 'success'
        else:
            date_prevue = date_age_min
            if aujourd_hui < date_prevue:
                statut, couleur = 'A venir', 'info'
            elif aujourd_hui == date_prevue:
                statut, couleur = "Aujourd_hui", 'warning'
            else:
                statut, couleur = 'En retard', 'danger'
        resultats.append({
            'nom': v['nom'], 'cle': cle, 'dose': v['dose'],
            'date_prevue': date_prevue, 'statut': statut, 'couleur': couleur,
        })
    dates_doses = {}
    for v in VACCINS_SERIE:
        cle = v['nom'] + '_' + v['dose']
        date_age_min = date_naissance + timedelta(weeks=v['semaines_min'])
        if v['precedent'] and v['precedent'] in dates_doses:
            date_intervalle = dates_doses[v['precedent']] + timedelta(weeks=4)
            date_finale = max(date_age_min, date_intervalle)
        else:
            date_finale = date_age_min
        if cle in vaccins_recus:
            statut, date_finale, couleur = 'Recu', vaccins_recus[cle], 'success'
            dates_doses[cle] = date_finale
        else:
            dates_doses[cle] = date_finale
            if aujourd_hui < date_finale:
                statut, couleur = 'A venir', 'info'
            elif aujourd_hui == date_finale:
                statut, couleur = "Aujourd_hui", 'warning'
            else:
                statut, couleur = 'En retard', 'danger'
        resultats.append({
            'nom': v['nom'] + ' dose ' + v['dose'], 'cle': cle, 'dose': v['dose'],
            'date_prevue': date_finale, 'statut': statut, 'couleur': couleur,
        })
    resultats.sort(key=lambda x: x['date_prevue'])
    return resultats
