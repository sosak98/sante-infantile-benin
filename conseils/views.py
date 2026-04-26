from django.shortcuts import render
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
