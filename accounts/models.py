from django.db import models
from django.contrib.auth.models import User

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20)
    quartier = models.CharField(max_length=100)

    def _str_(self):
        return f"{self.user.first_name} {self.user.last_name}"
