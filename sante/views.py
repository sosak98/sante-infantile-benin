import requests
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render

from .models import Etablissement

# Cadre geographique du Benin (limite les requetes a ce qui a du sens)
BENIN_OUEST, BENIN_SUD, BENIN_EST, BENIN_NORD = 0.70, 6.05, 3.95, 12.55
CACHE_TTL = 60 * 60 * 6  # 6 heures


def carte(request):
    # La serialisation JSON est geree cote gabarit par le filtre json_script
    # (echappe automatiquement le contenu : pas de sortie de contexte possible).
    etablissements = list(Etablissement.objects.values(
        "nom", "adresse", "telephone", "latitude", "longitude", "type_etab",
    ))
    return render(request, "sante/carte.html", {"etablissements": etablissements})


def _coordonnee(valeur, defaut, mini, maxi):
    """Force un float borne : empeche toute injection dans la requete Overpass
    (seuls des nombres peuvent ressortir d'ici)."""
    try:
        v = float(valeur)
    except (TypeError, ValueError):
        v = float(defaut)
    return min(max(v, mini), maxi)


def _elements_locaux(lat, lng, delta=0.2):
    """Convertit les etablissements de la base locale au format attendu par le JS."""
    qs = Etablissement.objects.filter(
        latitude__gte=lat - delta, latitude__lte=lat + delta,
        longitude__gte=lng - delta, longitude__lte=lng + delta,
    )[:500]
    elements = []
    for e in qs:
        amenity = {"pharmacie": "pharmacy", "hopital": "hospital",
                   "hopital_zone": "hospital"}.get(e.type_etab, "clinic")
        elements.append({
            "type": "node", "lat": e.latitude, "lon": e.longitude,
            "tags": {"name": e.nom, "amenity": amenity,
                     "phone": e.telephone or ""},
        })
    return elements


def _overpass(lat, lng):
    requete = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"hospital|clinic|pharmacy"](around:15000,{lat},{lng});
      way["amenity"~"hospital|clinic|pharmacy"](around:15000,{lat},{lng});
    );
    out center;
    """
    try:
        r = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": requete}, timeout=25,
            headers={"User-Agent": "SanteInfantileBenin/1.1"},
        )
        donnees = r.json()
        return donnees if donnees.get("elements") else None
    except Exception:
        return None


def etablissements_osm(request):
    """Enrichissement autour d'un point (Bénin uniquement).

    Securite : les coordonnees sont validees et bornees avant d'entrer dans la
    requete Overpass, et la reponse est mise en cache 6 h par zone pour ne pas
    servir de relais d'amplification vers l'API externe.
    """
    lat = _coordonnee(request.GET.get("lat"), 6.36, BENIN_SUD, BENIN_NORD)
    lng = _coordonnee(request.GET.get("lng"), 2.42, BENIN_OUEST, BENIN_EST)

    cle_cache = f"carte_osm:{lat:.2f}:{lng:.2f}"
    data = cache.get(cle_cache)
    if data is None:
        locaux = _elements_locaux(lat, lng)
        data = {"elements": locaux}
        # On ne sollicite Overpass que si la base locale est pauvre ici
        if len(locaux) < 5:
            data = _overpass(lat, lng) or data
        cache.set(cle_cache, data, CACHE_TTL)
    return JsonResponse(data)


def premiers_secours(request):
    """Module éducatif : gestes de premiers secours & signes de danger (0-5 ans)."""
    return render(request, "sante/premiers_secours.html")
