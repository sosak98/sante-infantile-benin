from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=150, blank=True)  # si vous stockez le prénom ici
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.username
