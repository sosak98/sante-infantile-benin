"""Marque les structures qui peuvent organiser des séances de vaccination PEV.

La base de production contient déjà les formations sanitaires, créées avant
l'ajout des champs de vaccination. Sans cette migration, `fait_vaccination`
resterait à False partout et la nouvelle page « Jours de vaccination »
paraîtrait vide.

On ne renseigne QUE la capacité à vacciner (déduite du type de structure).
Les jours de séance restent volontairement vides : ils sont déclarés par les
agents via l'espace professionnels. Afficher un jour inventé enverrait des
parents devant une porte close.
"""

from django.db import migrations

TYPES_VACCINATEURS = ('centre', 'hopital', 'hopital_zone')


def marquer(apps, schema_editor):
    Etablissement = apps.get_model('sante', 'Etablissement')
    Etablissement.objects.filter(type_etab__in=TYPES_VACCINATEURS).update(
        fait_vaccination=True
    )
    Etablissement.objects.filter(type_etab__in=('pharmacie', 'clinique')).update(
        fait_vaccination=False
    )


def demarquer(apps, schema_editor):
    Etablissement = apps.get_model('sante', 'Etablissement')
    Etablissement.objects.update(fait_vaccination=False)


class Migration(migrations.Migration):

    dependencies = [
        ('sante', '0002_alter_etablissement_options_etablissement_commune_and_more'),
    ]

    operations = [
        migrations.RunPython(marquer, demarquer),
    ]
