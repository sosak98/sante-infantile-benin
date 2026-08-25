from datetime import date
from types import SimpleNamespace
from django.shortcuts import render, get_object_or_404
from .models import Vaccin, ConseilNutritionnel
from .pev import planifier
from .seed_data import CONSEILS
from enfants.models import Enfant, VaccinRecu
from accounts.models import Parent


def _conseils_affichables(qs, age_mois=None, categorie='tous'):
    """Si la base est vide (Render sans seed), on affiche les conseils OMS du fichier."""
    if qs is not None and qs.exists():
        return list(qs)
    items = CONSEILS
    if age_mois is not None:
        items = [c for c in items if c['age_min_mois'] <= age_mois <= c['age_max_mois']]
    if categorie and categorie != 'tous':
        items = [c for c in items if c['categorie'] == categorie]
    return [SimpleNamespace(**c) for c in items]


def calendrier_vaccinal(request):
    vaccins = Vaccin.objects.all()
    return render(request, 'conseils/calendrier.html', {'vaccins': vaccins})


def conseils_nutritionnels(request):
    conseils = None
    age_mois = None
    categorie = None
    enfants = []
    parent = getattr(request.user, 'parent', None) if request.user.is_authenticated else None
    if parent:
        enfants = list(Enfant.objects.filter(parent=parent))

    if request.method == 'POST':
        enfant_id = request.POST.get('enfant_id')
        if enfant_id and parent:
            enfant = get_object_or_404(Enfant, id=enfant_id, parent=parent)
            today = date.today()
            age_mois = (today.year - enfant.date_naissance.year) * 12 + (
                today.month - enfant.date_naissance.month
            )
        else:
            age_mois = int(request.POST.get('age_mois') or 0)
        categorie = request.POST.get('categorie') or 'tous'
        conseils = ConseilNutritionnel.objects.filter(
            age_min_mois__lte=age_mois,
            age_max_mois__gte=age_mois,
        )
        if categorie != 'tous':
            conseils = conseils.filter(categorie=categorie)
        conseils = _conseils_affichables(conseils, age_mois, categorie)
    else:
        if len(enfants) == 1:
            e = enfants[0]
            today = date.today()
            age_mois = (today.year - e.date_naissance.year) * 12 + (today.month - e.date_naissance.month)
            conseils = ConseilNutritionnel.objects.filter(
                age_min_mois__lte=age_mois,
                age_max_mois__gte=age_mois,
            )
            conseils = _conseils_affichables(conseils, age_mois, 'tous')
        else:
            conseils = _conseils_affichables(ConseilNutritionnel.objects.all(), None, 'tous')
            age_mois = None
        categorie = 'tous'

    return render(request, 'conseils/nutrition.html', {
        'conseils': conseils,
        'age_mois': age_mois,
        'categorie': categorie,
        'enfants': enfants,
    })


def calculer_rdv(request):
    resultats = None
    enfants = []
    parent = getattr(request.user, 'parent', None) if request.user.is_authenticated else None
    if parent:
        enfants = list(Enfant.objects.filter(parent=parent))

    if request.method == 'POST':
        enfant = None
        enfant_id = request.POST.get('enfant_id')
        if enfant_id and parent:
            enfant = get_object_or_404(Enfant, id=enfant_id, parent=parent)
            date_naissance = enfant.date_naissance
        else:
            date_naissance = date.fromisoformat(request.POST.get('date_naissance'))

        vaccins_recus = {}
        noms_vaccins = request.POST.getlist('nom_vaccin[]')
        dates_vaccins = request.POST.getlist('date_vaccin[]')
        for nom, d in zip(noms_vaccins, dates_vaccins):
            if nom and d:
                vaccins_recus[nom] = date.fromisoformat(d)
                if enfant:
                    VaccinRecu.objects.update_or_create(
                        enfant=enfant,
                        nom_vaccin=nom,
                        defaults={'date_reelle': date.fromisoformat(d)},
                    )

        resultats = planifier(date_naissance, vaccins_recus)

    return render(request, 'conseils/rdv.html', {
        'resultats': resultats,
        'enfants': enfants,
    })
