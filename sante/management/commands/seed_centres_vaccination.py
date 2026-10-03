from django.core.management.base import BaseCommand
from sante.models import Etablissement

class Command(BaseCommand):
    help = 'Peuple les centres de vaccination de démonstration.'
    def handle(self, *args, **options):
        Etablissement.objects.update_or_create(
            nom='CS Akogbato',
            defaults={
                'type_etab': 'centre', 'adresse': 'Cotonou, Bénin', 'commune': 'Cotonou',
                'latitude': 6.35775, 'longitude': 2.35839, 'fait_vaccination': True,
                'jours_vaccination': 'lundi,mardi,mercredi,jeudi',
                'jours_vaccination_9mois': 'vendredi', 'jours_confirmes': True,
                'horaire_vaccination': '08h00 - 12h00', 'source_vaccination': 'centre',
                'precision_vaccination': 'Le vendredi est réservé aux vaccins de 9 mois (rougeole-rubéole, fièvre jaune, méningite A). Pas de séance le samedi ni le dimanche.',
            },
        )
        self.stdout.write(self.style.SUCCESS('Centre CS Akogbato synchronisé.'))
