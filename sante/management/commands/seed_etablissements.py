from django.core.management.base import BaseCommand
from sante.models import Etablissement

CENTRES = [
    ("CNHU-HKM", "hopital", "Camp Guézo, Cotonou", 6.3575, 2.4248, "+229 21301100"),
    ("CHU-MEL (HOMEL)", "hopital", "Suru-Léré, Cotonou", 6.3612, 2.4165, "+229 21313128"),
    ("Hôpital de zone de Suru-Léré", "hopital_zone", "Suru-Léré, Cotonou", 6.365, 2.405, ""),
    ("Hôpital de zone de Menontin", "hopital_zone", "Menontin, Cotonou", 6.384, 2.428, ""),
    ("Hôpital de zone d'Abomey-Calavi", "hopital_zone", "Abomey-Calavi", 6.448, 2.356, ""),
    ("Clinique de l'Union", "clinique", "Vodjè, Cotonou", 6.3705, 2.418, "+229 0152470505"),
    ("Polyclinique Les Cocotiers", "clinique", "Cocotiers, Cotonou", 6.352, 2.392, "+229 21301276"),
    ("Polyclinique Saint Michel (POSAM)", "clinique", "Cotonou", 6.365, 2.430, "+229 21318383"),
    ("Clinique du Lac", "clinique", "Lac, Cotonou", 6.368, 2.445, "+229 21313400"),
    ("Clinique Mahouna", "clinique", "Cotonou", 6.358, 2.400, "+229 21301435"),
    ("Clinique Fidjrossè", "clinique", "Fidjrossè, Cotonou", 6.349, 2.383, "+229 21306269"),
    ("Clinique Boni", "clinique", "Cotonou", 6.367, 2.425, "+229 21331437"),
    ("Centre de santé d'Akpakpa", "centre", "Akpakpa, Cotonou", 6.356, 2.448, ""),
    ("Centre de santé de Fidjrossè", "centre", "Fidjrossè, Cotonou", 6.347, 2.380, ""),
    ("Centre de santé de Godomey", "centre", "Godomey", 6.389, 2.345, ""),
    ("Pharmacie Marina", "pharmacie", "Sikècodji, Cotonou", 6.361, 2.437, "+229 21320246"),
    ("Pharmacie Midombo", "pharmacie", "Akpakpa, Cotonou", 6.355, 2.450, "+229 21339646"),
    ("Pharmacie de la Concorde", "pharmacie", "Cocotomey", 6.430, 2.340, "+229 21350452"),
    ("Pharmacie du Lac", "pharmacie", "Kpota, Calavi", 6.455, 2.350, "+229 94012395"),
    ("Pharmacie Château d'eau", "pharmacie", "Abomey-Calavi", 6.452, 2.355, "+229 95869246"),
    ("CHUD Borgou-Alibori (Parakou)", "hopital", "Parakou", 9.340, 2.630, ""),
    ("CHUD Ouémé-Plateau (Porto-Novo)", "hopital", "Porto-Novo", 6.497, 2.605, ""),
    ("Hôpital de zone d'Abomey", "hopital_zone", "Abomey", 7.183, 1.991, ""),
    ("Hôpital de zone de Bohicon", "hopital_zone", "Bohicon", 7.178, 2.067, ""),
    ("Hôpital de zone de Natitingou", "hopital_zone", "Natitingou", 10.304, 1.380, ""),
    ("Hôpital de zone de Lokossa", "hopital_zone", "Lokossa", 6.639, 1.717, ""),
    ("Hôpital de zone de Djougou", "hopital_zone", "Djougou", 9.700, 1.666, ""),
    ("Hôpital de zone de Kandi", "hopital_zone", "Kandi", 11.134, 2.939, ""),
    ("Hôpital de zone de Pobè", "hopital_zone", "Pobè", 6.980, 2.665, ""),
    ("Hôpital de zone d'Ouidah", "hopital_zone", "Ouidah", 6.363, 2.085, ""),
]


class Command(BaseCommand):
    help = "Ajoute hôpitaux, HZ, cliniques et pharmacies de Cotonou / Calavi s'ils manquent."

    def handle(self, *args, **options):
        n = 0
        for nom, typ, adr, lat, lng, tel in CENTRES:
            _, created = Etablissement.objects.get_or_create(
                nom=nom,
                defaults={
                    'type_etab': typ,
                    'adresse': adr,
                    'latitude': lat,
                    'longitude': lng,
                    'telephone': tel,
                },
            )
            if created:
                n += 1
        self.stdout.write(self.style.SUCCESS(f"{n} établissements ajoutés. Total : {Etablissement.objects.count()}"))
