from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Parent

class ParentRegisterForm(UserCreationForm):
    email = forms.EmailField(label="Adresse email")
    telephone = forms.CharField(max_length=20, label="Téléphone")
    quartier = forms.CharField(max_length=100, label="Quartier")
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmation du mot de passe", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'telephone', 'quartier', 'password1', 'password2']
        labels = {
            'username': "Nom d'utilisateur",
            'first_name': "Prénom",
            'last_name': "Nom de famille",
        }
        help_texts = {
            'username': "150 caractères maximum. Lettres, chiffres et @/./+/-/_ uniquement.",
            'password1': "Votre mot de passe doit contenir au moins 8 caractères.",
        }
