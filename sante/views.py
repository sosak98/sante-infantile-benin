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
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def creer_superuser(request):
    User = get_user_model()
    if not User.objects.filter(username='admin_sib').exists():
        User.objects.create_superuser('admin_sib', 'sante.infantile.benin@gmail.com', 'Admin2026!')
        return HttpResponse("Superutilisateur cree avec succes !")
    else:
        u = User.objects.get(username='admin_sib')
        u.set_password('Admin2026!')
        u.save()
        return HttpResponse("Mot de passe mis a jour !")
