from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Parent(models.Model):
    """Profil du parent, lié au compte utilisateur (User)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent')
    telephone = models.CharField(max_length=20)
    quartier = models.CharField(max_length=100, blank=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    nom = models.CharField(max_length=100, blank=True)
    prenom = models.CharField(max_length=100, blank=True)
    ville = models.CharField(max_length=100, blank=True, default='Cotonou')
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)

    def __str__(self):
        return self.user.username

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip() or self.user.username


class Profile(models.Model):
    """Ancien profil complémentaire (conservé pour compatibilité)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=150, blank=True)
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.username


class PhoneOTP(models.Model):
    """Stocke les codes OTP envoyés aux numéros de téléphone."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_otps', null=True, blank=True)
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    def is_valid(self, expiry_minutes=10):
        return (not self.verified) and (timezone.now() <= self.created_at + timedelta(minutes=expiry_minutes))

    def __str__(self):
        return f"OTP {self.phone} ({'v' if self.verified else 'nv'})"
