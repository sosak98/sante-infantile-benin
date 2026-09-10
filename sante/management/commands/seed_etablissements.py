"""
Peuple la table Etablissement avec les formations sanitaires du Benin.

Deux sources :
1. le fichier embarque `sante/data/formations_sanitaires_bj.json`
   (961 structures : hopitaux, centres de sante, pharmacies, cliniques,
   extraction OpenStreetMap)
2. l'option --osm : requete Overpass live sur TOUT le territoire
   (au lieu de Cotonou seul dans l'ancienne version) pour completer
   avec les structures les plus recentes.

La commande est idempotente : relancer ne cree pas de doublons
(dedoublonnage sur nom + coordonnees arrondies).

Usage :
    python manage.py seed_etablissements           # rapide (fichier)
    python manage.py seed_etablissements --osm     # + enrichissement live
"""
import json
from pathlib import Path

import requests
from django.core.management.base import BaseCommand

from sante.models import Etablissement

DONNEES = Path(__file__).resolve().parents[2] / "data" / "formations_sanitaires_bj.json"

# categories du fichier embarque -> types du modele
TYPES_BJ = {
    "hopital": "hopital",
    "pharmacie": "pharmacie",
    "centre_sante": "centre",
    "medecin": "clinique",
    "sante_autre": "centre",
    "laboratoire": "centre",
}

# balises OSM -> types du modele
TYPES_OSM = {
    "pharmacy": "pharmacie",
    "hospital": "hopital",
    "clinic": "centre",
    "doctors": "clinique",
}

# Cadre geographique complet du Benin (sud, ouest, nord, est)
BBOX_BENIN = "6.05,0.70,12.55,3.95"


def _cle(nom, lat, lng):
    return (nom.strip().lower(), round(float(lat), 3), round(float(lng), 3))


class Command(BaseCommand):
    help = "Importe les formations sanitaires du Benin (fichier + option OSM live)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--osm", action="store_true",
            help="Enrichir via une requete Overpass live sur tout le Benin (lent).",
        )

    def handle(self, *args, **options):
        existants = {_cle(e.nom, e.latitude, e.longitude)
                     for e in Etablissement.objects.all()}
        ajoutes = 0
        ajoutes += self._depuis_fichier(existants)
        if options["osm"]:
            ajoutes += self._depuis_overpass(existants)
        self.stdout.write(self.style.SUCCESS(
            f"Termine : {ajoutes} etablissements ajoutes "
            f"({Etablissement.objects.count()} au total)."))

    def _depuis_fichier(self, existants):
        donnees = json.loads(DONNEES.read_text(encoding="utf-8"))
        lieux = donnees.get("lieux", [])
        a_creer = []
        for lieu in lieux:
            type_etab = TYPES_BJ.get(lieu.get("c"))
            if not type_etab or not lieu.get("n"):
                continue
            cle = _cle(lieu["n"], lieu["lat"], lieu["lon"])
            if cle in existants:
                continue
            existants.add(cle)
            a_creer.append(Etablissement(
                nom=lieu["n"][:200],
                type_etab=type_etab,
                adresse="Bénin",
                latitude=lieu["lat"],
                longitude=lieu["lon"],
                telephone=(lieu.get("tel") or "")[:20],
            ))
        Etablissement.objects.bulk_create(a_creer, batch_size=500)
        self.stdout.write(f"  fichier embarque : +{len(a_creer)}")
        return len(a_creer)

    def _depuis_overpass(self, existants):
        requete = f"""
        [out:json][timeout:180];
        (
          node["amenity"~"hospital|clinic|pharmacy|doctors"]({BBOX_BENIN});
          way["amenity"~"hospital|clinic|pharmacy|doctors"]({BBOX_BENIN});
          node["healthcare"~"centre|dispensary"]({BBOX_BENIN});
          way["healthcare"~"centre|dispensary"]({BBOX_BENIN});
        );
        out center tags;
        """
        try:
            r = requests.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": requete}, timeout=200,
                headers={"User-Agent": "SanteInfantileBenin/1.1"},
            )
            elements = r.json().get("elements", [])
        except Exception as e:
            self.stderr.write(f"  Overpass indisponible ({e}), on garde le fichier.")
            return 0

        ajoutes = 0
        a_creer = []
        for el in elements:
            tags = el.get("tags", {})
            nom = (tags.get("name") or "").strip()
            if not nom:
                continue
            if el.get("lat") is not None:
                lat, lng = el["lat"], el["lon"]
            else:
                centre = el.get("center") or {}
                lat, lng = centre.get("lat"), centre.get("lon")
            if not lat or not lng:
                continue
            type_etab = TYPES_OSM.get(tags.get("amenity", ""), "centre")
            cle = _cle(nom, lat, lng)
            if cle in existants:
                continue
            existants.add(cle)
            ville = (tags.get("addr:city") or tags.get("addr:suburb")
                     or tags.get("is_in") or "")
            adresse = f"{ville}, Bénin" if ville else "Bénin"
            a_creer.append(Etablissement(
                nom=nom[:200],
                type_etab=type_etab,
                adresse=adresse[:300],
                latitude=lat,
                longitude=lng,
                telephone=(tags.get("phone") or tags.get("contact:phone") or "")[:20],
            ))
            ajoutes += 1
        Etablissement.objects.bulk_create(a_creer, batch_size=500)
        self.stdout.write(f"  Overpass live : +{ajoutes}")
        return ajoutes
