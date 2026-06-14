import json
import requests
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Etablissement
from conseils.seed_vaccins import *


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


@csrf_exempt
def charger_seeds(request):
    url = 'https://overpass-api.de/api/interpreter'
    query = '[out:json][timeout:60];(node["amenity"="hospital"](6.2,2.2,6.5,2.7);node["amenity"="clinic"](6.2,2.2,6.5,2.7);node["amenity"="pharmacy"](6.2,2.2,6.5,2.7);way["amenity"="hospital"](6.2,2.2,6.5,2.7);way["amenity"="pharmacy"](6.2,2.2,6.5,2.7););out center;'

    try:
        response = requests.get(
            url,
            params={'data': query},
            timeout=60,
            headers={'User-Agent': 'SanteInfantileBenin/1.0'}
        )
        data = response.json()
        elements = data.get('elements', [])
        ajoutes = 0

        for element in elements:
            tags = element.get('tags', {})
            nom = tags.get('name', '')
            if not nom:
                continue
            amenity = tags.get('amenity', '')
            type_etab = 'pharmacie' if amenity == 'pharmacy' else 'centre'

            if element.get('type') == 'node':
                lat = element.get('lat')
                lng = element.get('lon')
            else:
                center = element.get('center', {})
                lat = center.get('lat')
                lng = center.get('lon')

            if not lat or not lng:
                continue

            telephone = tags.get('phone', '')
            adresse = tags.get('addr:street', 'Cotonou, Benin')

            if not Etablissement.objects.filter(nom=nom).exists():
                Etablissement.objects.create(
                    nom=nom,
                    type_etab=type_etab,
                    adresse=adresse,
                    latitude=lat,
                    longitude=lng,
                    telephone=telephone
                )
                ajoutes += 1

        return HttpResponse(f"✅ {ajoutes} etablissements ajoutes ! Total elements: {len(elements)}")

    except Exception as e:
        return HttpResponse(f"❌ Erreur: {str(e)}")
