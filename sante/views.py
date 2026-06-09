import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
from .models import Etablissement

def carte(request):
    etablissements = list(Etablissement.objects.values(
        'nom', 'adresse', 'telephone', 'latitude', 'longitude', 'type_etab'
    ))
    return render(request, 'sante/carte.html', {
        'etablissements_json': json.dumps(etablissements)
    })

def etablissements_osm(request):
    lat = request.GET.get('lat', '6.36')
    lng = request.GET.get('lng', '2.42')
    
    query = f'''
    [out:json][timeout:25];
    (
        node["amenity"="hospital"](around:5000,{lat},{lng});
        node["amenity"="clinic"](around:5000,{lat},{lng});
        node["amenity"="pharmacy"](around:5000,{lat},{lng});
        way["amenity"="hospital"](around:5000,{lat},{lng});
    );
    out center;
    '''
    
    try:
        response = requests.post(
            'https://overpass-api.de/api/interpreter',
            data=query,
            timeout=25
        )
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def charger_seeds(request):
    from conseils.seed_vaccins import *
    return HttpResponse("Seeds charges !")
