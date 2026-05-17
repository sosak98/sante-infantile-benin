import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'santeinfantile.settings')
django.setup()

from conseils.models import Vaccin

f Vaccin.objects.exists():
    print("Vaccins deja presents - skip")
    import sys
    sys.exit(0)

Vaccin.objects.all().delete()

vaccins = [
    # Naissance
    {"nom": "BCG", "age_affichage": "Naissance", "age_min_mois": 0, "description": "Protection contre la tuberculose", "obligatoire": True},
    {"nom": "VPO 0 (Polio oral)", "age_affichage": "Naissance", "age_min_mois": 0, "description": "1ère dose vaccin contre la poliomyélite", "obligatoire": True},
    {"nom": "Hépatite B", "age_affichage": "Naissance", "age_min_mois": 0, "description": "1ère dose protection contre l'hépatite B", "obligatoire": True},

    # 6 semaines
    {"nom": "Pentavalent 1", "age_affichage": "6 semaines", "age_min_mois": 2, "description": "Diphtérie, Tétanos, Coqueluche, Hépatite B, Hib — 1ère dose", "obligatoire": True},
    {"nom": "VPO 1", "age_affichage": "6 semaines", "age_min_mois": 2, "description": "2ème dose vaccin polio oral", "obligatoire": True},
    {"nom": "Pneumocoque 1 (PCV)", "age_affichage": "6 semaines", "age_min_mois": 2, "description": "Protection contre les pneumonies et méningites — 1ère dose", "obligatoire": True},

    # 10 semaines
    {"nom": "Pentavalent 2", "age_affichage": "10 semaines", "age_min_mois": 3, "description": "Diphtérie, Tétanos, Coqueluche, Hépatite B, Hib — 2ème dose", "obligatoire": True},
    {"nom": "VPO 2", "age_affichage": "10 semaines", "age_min_mois": 3, "description": "3ème dose vaccin polio oral", "obligatoire": True},
    {"nom": "Pneumocoque 2 (PCV)", "age_affichage": "10 semaines", "age_min_mois": 3, "description": "Protection contre les pneumonies — 2ème dose", "obligatoire": True},

    # 14 semaines
    {"nom": "Pentavalent 3", "age_affichage": "14 semaines", "age_min_mois": 4, "description": "Diphtérie, Tétanos, Coqueluche, Hépatite B, Hib — 3ème dose", "obligatoire": True},
    {"nom": "VPO 3", "age_affichage": "14 semaines", "age_min_mois": 4, "description": "4ème dose vaccin polio oral", "obligatoire": True},
    {"nom": "Pneumocoque 3 (PCV)", "age_affichage": "14 semaines", "age_min_mois": 4, "description": "Protection contre les pneumonies — 3ème dose", "obligatoire": True},

    # 6 mois
    {"nom": "Vaccin Antipaludique 1 (RTS,S)", "age_affichage": "6 mois", "age_min_mois": 6, "description": "1ère dose vaccin contre le paludisme — introduit au Bénin en 2024", "obligatoire": True},

    # 7 mois
    {"nom": "Vaccin Antipaludique 2 (RTS,S)", "age_affichage": "7 mois", "age_min_mois": 7, "description": "2ème dose vaccin contre le paludisme", "obligatoire": True},

    # 9 mois
    {"nom": "VAR (Rougeole-Rubéole)", "age_affichage": "9 mois", "age_min_mois": 9, "description": "Protection contre la rougeole et la rubéole", "obligatoire": True},
    {"nom": "VAA (Fièvre jaune)", "age_affichage": "9 mois", "age_min_mois": 9, "description": "Protection contre la fièvre jaune — obligatoire au Bénin", "obligatoire": True},
    {"nom": "MenA (Méningite A)", "age_affichage": "9 mois", "age_min_mois": 9, "description": "Protection contre la méningite à méningocoque A", "obligatoire": True},
    {"nom": "Vaccin Antipaludique 3 (RTS,S)", "age_affichage": "9 mois", "age_min_mois": 9, "description": "3ème dose vaccin contre le paludisme", "obligatoire": True},

    # 18-23 mois
    {"nom": "Vaccin Antipaludique 4 (RTS,S)", "age_affichage": "18-23 mois", "age_min_mois": 18, "age_max_mois": 23, "description": "4ème et dernière dose vaccin contre le paludisme", "obligatoire": True},
    {"nom": "VAR 2 (Rappel Rougeole)", "age_affichage": "18 mois", "age_min_mois": 18, "description": "Rappel vaccin rougeole-rubéole", "obligatoire": True},
]

for v in vaccins:
    Vaccin.objects.create(**v)

print(f"✅ {len(vaccins)} vaccins ajoutés avec succès !")
