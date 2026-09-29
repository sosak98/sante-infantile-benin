from datetime import date
from types import SimpleNamespace
from django.shortcuts import render, get_object_or_404
from .models import Vaccin, ConseilNutritionnel
from .pev import (
    CALENDRIER_PEV,
    SUPPLEMENTATIONS,
    calendrier_affichable,
    normaliser_cle,
    planifier,
)
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
    """Calendrier PEV de référence.

    La table `Vaccin` sert de cache administrable, mais la page ne doit JAMAIS
    être vide : si le seed n'a pas tourné, on affiche directement le calendrier
    de référence de `conseils/pev.py`.
    """
    vaccins = calendrier_affichable()
    return render(request, 'conseils/calendrier.html', {
        'vaccins': vaccins,
        'nb_doses': len(vaccins),
        'supplementations': SUPPLEMENTATIONS,
    })


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

    erreur = None
    if request.method == 'POST':
        enfant = None
        date_naissance = None
        enfant_id = request.POST.get('enfant_id')
        if enfant_id and parent:
            enfant = get_object_or_404(Enfant, id=enfant_id, parent=parent)
            date_naissance = enfant.date_naissance
        else:
            # Une saisie libre invalide provoquait une erreur 500 : on la
            # traite comme une erreur de formulaire.
            try:
                date_naissance = date.fromisoformat(
                    (request.POST.get('date_naissance') or '').strip()
                )
            except ValueError:
                erreur = "Merci d'indiquer une date de naissance valide."
            else:
                if date_naissance > date.today():
                    erreur = "La date de naissance ne peut pas être dans le futur."
                    date_naissance = None

        if date_naissance is None:
            return render(request, 'conseils/rdv.html', {
                'resultats': None,
                'enfants': enfants,
                'calendrier': CALENDRIER_PEV,
                'erreur': erreur,
            })

        # Doses déjà enregistrées pour cet enfant (elles ne doivent pas être
        # perdues quand le parent recalcule son planning).
        vaccins_recus = {}
        if enfant:
            for recu in VaccinRecu.objects.filter(enfant=enfant):
                cle = normaliser_cle(recu.nom_vaccin)
                if cle:
                    vaccins_recus[cle] = recu.date_reelle

        noms_vaccins = request.POST.getlist('nom_vaccin[]')
        dates_vaccins = request.POST.getlist('date_vaccin[]')
        for nom, d in zip(noms_vaccins, dates_vaccins):
            cle = normaliser_cle(nom)
            if not cle or not d:
                continue
            try:
                jour = date.fromisoformat(d)
            except ValueError:
                continue
            # Une date de vaccination ne peut pas précéder la naissance
            # ni être dans le futur.
            if jour < date_naissance or jour > date.today():
                continue
            vaccins_recus[cle] = jour
            if enfant:
                # On enregistre la clé normalisée : plus de libellés divergents.
                VaccinRecu.objects.update_or_create(
                    enfant=enfant,
                    nom_vaccin=cle,
                    defaults={'date_reelle': jour},
                )

        resultats = planifier(date_naissance, vaccins_recus)

    return render(request, 'conseils/rdv.html', {
        'resultats': resultats,
        'enfants': enfants,
        'calendrier': CALENDRIER_PEV,
        'erreur': erreur,
    })
