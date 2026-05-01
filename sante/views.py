import json
from django.shortcuts import render
from .models import Etablissement

def carte(request):
    etablissements = list(Etablissement.objects.values(
        'nom', 'adresse', 'telephone', 'latitude', 'longitude', 'type_etab'
    ))
    return render(request, 'sante/carte.html', {
        'etablissements_json': json.dumps(etablissements)
    })
