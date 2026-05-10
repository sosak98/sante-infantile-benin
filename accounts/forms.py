from django import forms
from django.contrib.auth.models import User
from .models import Parent

class ParentRegisterForm(forms.Form):
    telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Numéro de téléphone',
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Mot de passe',
            'id': 'password1'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirmer le mot de passe',
            'id': 'password2'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        telephone = cleaned_data.get('telephone')

        if telephone and not telephone.isdigit():
            raise forms.ValidationError("Le numéro de téléphone doit contenir uniquement des chiffres !")

        if telephone and len(telephone) < 8:
            raise forms.ValidationError("Le numéro de téléphone doit contenir au moins 8 chiffres !")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas !")

        if telephone and User.objects.filter(username=telephone).exists():
            raise forms.ValidationError("Ce numéro est déjà utilisé !")

        return cleaned_data

    def save(self):
        telephone = self.cleaned_data['telephone']
        password = self.cleaned_data['password1']
        user = User.objects.create_user(
            username=telephone,
            password=password
        )
        Parent.objects.create(
            user=user,
            telephone=telephone,
            quartier=''
        )
        return user
