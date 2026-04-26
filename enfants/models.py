from django.db import models
from accounts.models import Parent

class Enfant(models.Model):
    SEXE_CHOICES = (
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    )
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)

    def __str__(self):
        return f"{self.nom} ({self.get_sexe_display()})"

class MesureEnfant(models.Model):
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE)
    date_mesure = models.DateField(auto_now_add=True)
    poids = models.FloatField(help_text="Poids en kg")
    taille = models.FloatField(help_text="Taille en cm")
    muac = models.FloatField(help_text="Périmètre brachial en cm", null=True, blank=True)

    def __str__(self):
        return f"Mesure de {self.enfant.nom} le {self.date_mesure}"
