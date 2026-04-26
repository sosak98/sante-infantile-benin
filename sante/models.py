from django.db import models

class Etablissement(models.Model):
    TYPES = (
        ('centre', 'Centre de Santé'),
        ('pharmacie', 'Pharmacie'),
    )
    nom = models.CharField(max_length=200)
    type_etab = models.CharField(max_length=20, choices=TYPES)
    adresse = models.CharField(max_length=300)
    latitude = models.FloatField()
    longitude = models.FloatField()
    telephone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.nom} ({self.get_type_etab_display()})"
