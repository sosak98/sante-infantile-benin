from datetime import date
from django.shortcuts import render, get_object_or_404
from .models import Vaccin, ConseilNutritionnel
from .pev import planifier
from enfants.models import Enfant, VaccinRecu
from accounts.models import Parent


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
    elif len(enfants) == 1:
        e = enfants[0]
        today = date.today()
        age_mois = (today.year - e.date_naissance.year) * 12 + (today.month - e.date_naissance.month)
        conseils = ConseilNutritionnel.objects.filter(
            age_min_mois__lte=age_mois,
            age_max_mois__gte=age_mois,
        )
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
