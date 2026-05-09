import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'santeinfantile.settings')
django.setup()

from sante.models import Etablissement

print("Recuperation des etablissements...")

url = 'https://overpass-api.de/api/interpreter'
query = '[out:json][timeout:60];(node["amenity"="hospital"](6.2,2.2,6.5,2.7);node["amenity"="clinic"](6.2,2.2,6.5,2.7);node["amenity"="pharmacy"](6.2,2.2,6.5,2.7);way["amenity"="hospital"](6.2,2.2,6.5,2.7);way["amenity"="pharmacy"](6.2,2.2,6.5,2.7););out center;'

try:
    response = requests.get(
        url,
        params={'data': query},
        timeout=60,
        headers={'User-Agent': 'SanteInfantileBenin/1.0'}
    )
    print(f"Status: {response.status_code}")
    print(f"Reponse: {response.text[:200]}")
    data = response.json()
    elements = data.get('elements', [])
    print(f"{len(elements)} etablissements trouves")

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
            print(f"Ajoute: {nom}")

    print(f"✅ {ajoutes} etablissements ajoutes !")

except Exception as e:
    print(f"Erreur: {e}")
