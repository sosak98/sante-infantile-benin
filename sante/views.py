from django.shortcuts import render
from .models import Etablissement

def carte(request):
    etablissements = list(Etablissement.objects.values())  # conversion en liste de dictionnaires
    return render(request, 'sante/carte.html', {'etablissements': etablissements})
