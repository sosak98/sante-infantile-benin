"""Peuple les centres de vaccination dont le programme a été relevé sur place.

Les neuf centres ci-dessous ont été visités : leur programme vient du centre
lui-même (`source_vaccination='centre'`, `jours_confirmes=True`). Ils ne
raisonnent pas « avant 9 mois / 9 mois » mais **par vaccin** : le BCG le lundi,
le Pentavalent le mardi, la vitamine A le mercredi… D'où le programme détaillé
`programme_vaccination`, dont `jours_vaccination` se déduit (pas de double
saisie).

Deux règles :

- **aucune coordonnée inventée** : seules deux adresses nous sont connues.
  Les sept autres restent à 0.0 / commune vide jusqu'à leur saisie dans
  l'administration — un centre mal placé envoie une famille au mauvais endroit ;
- le RTS,S (vaccin antipaludique) n'est déployé que dans certaines zones :
  il n'est proposé que par CS Akogbato.

La commande est idempotente : `update_or_create` sur le nom.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from sante.models import CODES_JOURS, Etablissement

# Groupes de vaccins non déployés dans tous les centres : le RTS,S n'arrive
# que dans certaines zones, seul CS Akogbato le propose ici.
NON_PROPOSE_PARTOUT = 'rtss'


def _tous():
    return {'mode': 'tous'}


def _seulement(*series):
    return {'mode': 'seulement', 'series': list(series)}


def _tous_sauf(*series):
    return {'mode': 'tous_sauf', 'series': list(series)}


# Programme relevé auprès de chaque centre (lundi → vendredi).
CENTRES = [
    {
        'nom': 'CS Akogbato',
        'commune': 'Cotonou',
        'adresse': 'Cotonou, Bénin',
        'latitude': 6.35775,
        'longitude': 2.35839,
        # Horaire communiqué par le centre ; il n'est pas inventé ici.
        'horaire_vaccination': '08h00 - 12h00',
        'programme_vaccination': {
            'lundi': _tous_sauf('9mois'),
            'mardi': _tous_sauf('9mois'),
            'mercredi': _tous_sauf('9mois'),
            'jeudi': _tous_sauf('9mois'),
            'vendredi': _tous(),
        },
        # Seul centre qui propose le vaccin antipaludique.
        'vaccins_non_proposes': '',
    },
    {
        'nom': 'CS Dowa',
        'programme_vaccination': {
            'lundi': _seulement('bcg', 'vpo', 'vpo_naissance'),
            'mardi': _seulement('penta', 'pcv', 'rota', 'vpi'),
            'mercredi': _seulement('vitamine_a'),
            'jeudi': _seulement('penta', 'pcv', 'rota', 'vpi'),
            'vendredi': _seulement('9mois', 'var'),
        },
    },
    {
        'nom': 'CS Sori',
        'programme_vaccination': {
            'jeudi': _seulement('bcg'),
            'vendredi': _tous(),
        },
    },
    {
        'nom': 'CS Aledjo',
        'programme_vaccination': {
            'mardi': _tous(),
        },
    },
    {
        'nom': 'CSC Materi',
        'programme_vaccination': {
            'lundi': _tous(),
            'mercredi': _tous_sauf('bcg', 'var'),
            'vendredi': _tous(),
        },
    },
    {
        'nom': 'CS Semere',
        'programme_vaccination': {
            'vendredi': _tous(),
        },
    },
    {
        'nom': 'CS Nikki',
        'programme_vaccination': {
            'lundi': _seulement('bcg'),
            'mardi': _tous_sauf('bcg'),
            'mercredi': _tous_sauf('bcg'),
            'jeudi': _tous_sauf('bcg'),
            'vendredi': _tous_sauf('bcg'),
        },
    },
    {
        'nom': 'CS Bohicon 2',
        'commune': 'Bohicon',
        'adresse': 'Bohicon, Bénin',
        'latitude': 7.17926,
        'longitude': 2.06601,
        'programme_vaccination': {
            'lundi': _tous(),
            'mardi': _tous(),
            'mercredi': _tous(),
            'jeudi': _tous(),
            'vendredi': _tous(),
        },
    },
    {
        'nom': 'CS Kpolokoue',
        'programme_vaccination': {
            'lundi': _tous(),
            'vendredi': _tous(),
        },
    },
]


class Command(BaseCommand):
    help = 'Peuple les centres de vaccination réels et leur programme (relevé sur place).'

    def handle(self, *args, **options):
        crees = 0
        for fiche in CENTRES:
            fiche = dict(fiche)
            programme = fiche.pop('programme_vaccination')
            # `jours_vaccination` se déduit des clés du programme.
            jours = ','.join(code for code in CODES_JOURS if code in programme)
            defaults = {
                'type_etab': 'centre',
                'adresse': fiche.get('adresse', 'Bénin'),
                'commune': fiche.get('commune', ''),
                'latitude': fiche.get('latitude', 0.0),
                'longitude': fiche.get('longitude', 0.0),
                'fait_vaccination': True,
                'jours_vaccination': jours,
                'jours_confirmes': True,
                'precision_vaccination': '',
                'source_vaccination': 'centre',
                'maj_vaccination': timezone.now(),
                'programme_vaccination': programme,
                'vaccins_non_proposes': fiche.get('vaccins_non_proposes', NON_PROPOSE_PARTOUT),
            }
            # On ne touche pas à l'horaire ni au téléphone des centres dont on
            # ne sait rien : ils se renseignent dans l'administration.
            if fiche.get('horaire_vaccination'):
                defaults['horaire_vaccination'] = fiche['horaire_vaccination']
            _, cree = Etablissement.objects.update_or_create(
                nom=fiche['nom'], defaults=defaults,
            )
            crees += int(cree)
        self.stdout.write(self.style.SUCCESS(
            f'{len(CENTRES)} centres de vaccination synchronisés '
            f'({crees} créés, {len(CENTRES) - crees} mis à jour).'
        ))
