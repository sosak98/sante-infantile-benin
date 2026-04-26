from django.db import models

class Vaccin(models.Model):
    nom = models.CharField(max_length=100)
    age_affichage = models.CharField(max_length=50)
    age_min_mois = models.IntegerField()
    age_max_mois = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    obligatoire = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nom} ({self.age_affichage})"

    class Meta:
        ordering = ['age_min_mois']


class ConseilNutritionnel(models.Model):
    CATEGORIE_CHOICES = (
        ('aliment', 'Type d\'aliment'),
        ('probleme', 'Problème de santé'),
    )
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    age_min_mois = models.IntegerField(help_text="Âge minimum en mois")
    age_max_mois = models.IntegerField(help_text="Âge maximum en mois")
    mots_cles = models.CharField(max_length=200, blank=True, help_text="Ex: diarrhée, fièvre, protéines")

    def __str__(self):
        return f"{self.titre} ({self.age_min_mois}-{self.age_max_mois} mois)"

    class Meta:
        ordering = ['age_min_mois']
