from django.db import models
from django.contrib.auth.models import User

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20)
    nom = models.CharField(max_length=100, blank=True)
    prenom = models.CharField(max_length=100, blank=True)
    quartier = models.CharField(max_length=100, blank=True)
    ville = models.CharField(max_length=100, blank=True, default='Cotonou')
    date_inscription = models.DateTimeField(auto_now_add=True)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.telephone})"
