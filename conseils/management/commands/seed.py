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
        n = 0
        for c in CONSEILS:
            _, created = ConseilNutritionnel.objects.get_or_create(
                titre=c['titre'],
                defaults=c,
            )
            if created:
                n += 1
        self.stdout.write(self.style.SUCCESS(f"Conseils : {n} ajoutés, total {ConseilNutritionnel.objects.count()}."))
