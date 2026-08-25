from django.core.management.base import BaseCommand
from conseils.models import Vaccin, ConseilNutritionnel
from conseils.seed_data import VACCINS, CONSEILS


class Command(BaseCommand):
    help = "Charge les données de référence (vaccins PEV + conseils nutritionnels) si les tables sont vides."

    def handle(self, *args, **options):
        # Vaccins
        if Vaccin.objects.exists():
            self.stdout.write(self.style.WARNING(f"Vaccins : déjà {Vaccin.objects.count()} présents, ignoré."))
        else:
            Vaccin.objects.bulk_create([Vaccin(**v) for v in VACCINS])
            self.stdout.write(self.style.SUCCESS(f"✅ {len(VACCINS)} vaccins ajoutés."))

        # Conseils nutritionnels
        if ConseilNutritionnel.objects.exists():
            self.stdout.write(self.style.WARNING(f"Conseils : déjà {ConseilNutritionnel.objects.count()} présents, ignoré."))
        else:
            ConseilNutritionnel.objects.bulk_create([ConseilNutritionnel(**c) for c in CONSEILS])
            self.stdout.write(self.style.SUCCESS(f"✅ {len(CONSEILS)} conseils nutritionnels ajoutés."))
