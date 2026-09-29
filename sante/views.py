import requests
from django.core.cache import cache
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render

from .models import (
    CODES_JOURS,
    JOURS_SEMAINE,
    LIBELLES_JOURS,
    Etablissement,
    code_du_jour,
)

# Cadre geographique du Benin (limite les requetes a ce qui a du sens)
BENIN_OUEST, BENIN_SUD, BENIN_EST, BENIN_NORD = 0.70, 6.05, 3.95, 12.55
CACHE_TTL = 60 * 60 * 6  # 6 heures

# Types de structures susceptibles d'organiser des seances de vaccination PEV
TYPES_VACCINATEURS = ('centre', 'hopital', 'hopital_zone')


def carte(request):
    # La serialisation JSON est geree cote gabarit par le filtre json_script
    # (echappe automatiquement le contenu : pas de sortie de contexte possible).
    etablissements = []
    for e in Etablissement.objects.all():
        etablissements.append({
            'nom': e.nom,
            'adresse': e.adresse,
            'telephone': e.telephone,
            'latitude': e.latitude,
            'longitude': e.longitude,
            'type_etab': e.type_etab,
            'vaccination': e.fait_vaccination,
            'jours': e.jours_liste,
            'jours_txt': e.jours_affichage,
            'horaire': e.horaire_vaccination,
        })
    return render(request, "sante/carte.html", {
        "etablissements": etablissements,
        "jours_semaine": JOURS_SEMAINE,
        "jour_actuel": code_du_jour(),
    })


def jours_vaccination(request):
    """Où et quand faire vacciner son enfant, par jour de la semaine.

    Le filtre par défaut est le jour courant : la question d'un parent est
    presque toujours « où puis-je aller aujourd'hui ? ».
    """
    jour = (request.GET.get('jour') or '').strip().lower()
    if jour not in CODES_JOURS and jour != 'tous':
        jour = code_du_jour()
    recherche = (request.GET.get('q') or '').strip()

    centres = Etablissement.objects.filter(fait_vaccination=True)
    if recherche:
        centres = centres.filter(
            Q(nom__icontains=recherche)
            | Q(commune__icontains=recherche)
            | Q(adresse__icontains=recherche)
        )

    # Les centres dont les jours sont publiés, filtrés sur le jour demandé.
    publies = centres.exclude(jours_vaccination='')
    if jour != 'tous':
        publies = publies.filter(jours_vaccination__contains=jour)

    # Les centres qui vaccinent mais n'ont pas communiqué leurs jours : on les
    # montre à part plutôt que de les cacher ou d'inventer un horaire.
    sans_jours = centres.filter(jours_vaccination='')

    return render(request, 'sante/jours_vaccination.html', {
        'centres': publies.order_by('nom')[:300],
        'nb_publies': publies.count(),
        'sans_jours': sans_jours.order_by('nom')[:60],
        'nb_sans_jours': sans_jours.count(),
        'recherche': recherche,
        'jour': jour,
        'jour_libelle': LIBELLES_JOURS.get(jour, 'Toute la semaine'),
        'jours_semaine': JOURS_SEMAINE,
        'jour_actuel': code_du_jour(),
    })


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
