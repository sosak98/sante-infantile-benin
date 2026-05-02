from django.db import models
from accounts.models import Parent

class Enfant(models.Model):
    SEXE_CHOICES = (
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    )
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    class Meta:
        ordering = ['date_naissance']

class VaccinRecu(models.Model):
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE, related_name='vaccins_recus')
    nom_vaccin = models.CharField(max_length=100)
    date_reelle = models.DateField()
    remarque = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nom_vaccin} - {self.enfant.prenom} ({self.date_reelle})"

    class Meta:
        ordering = ['date_reelle']

class MesureEnfant(models.Model):
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE)
    date_mesure = models.DateField(auto_now_add=True)
    poids = models.FloatField(help_text="Poids en kg")
    taille = models.FloatField(help_text="Taille en cm")
    muac = models.FloatField(help_text="Périmètre brachial en cm", null=True, blank=True)

    def __str__(self):
        return f"Mesure de {self.enfant.prenom} le {self.date_mesure}"
