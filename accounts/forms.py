from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Parent


class PhoneSendForm(forms.Form):
    phone = forms.CharField(max_length=20, label="Numéro de téléphone",
                            widget=forms.TextInput(attrs={'placeholder': '+229XXXXXXXX'}))


class PhoneVerifyForm(forms.Form):
    phone = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(max_length=6, label="Code reçu",
                           widget=forms.TextInput(attrs={'placeholder': '123456'}))


class ParentRegisterForm(forms.Form):
    """Création de compte : numéro de téléphone (utilisé comme identifiant) + mot de passe."""
    telephone = forms.CharField(
        max_length=20,
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={
            'placeholder': '+229 97 00 00 00',
            'autocomplete': 'tel',
            'inputmode': 'tel',
            'class': 'form-control',
        }),
    )
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'autocomplete': 'new-password', 'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'autocomplete': 'new-password', 'class': 'form-control'}),
    )
    accepte_conditions = forms.BooleanField(
        required=True,
        label="J'ai lu et j'accepte les Conditions d'utilisation et la Politique de confidentialité",
        error_messages={
            'required': "Vous devez accepter les conditions d'utilisation et la politique de confidentialité pour créer un compte."
        },
        widget=forms.CheckboxInput(),
    )

    def clean_telephone(self):
        telephone = self.cleaned_data['telephone'].strip()
        if not telephone:
            raise ValidationError("Le numéro de téléphone est obligatoire.")
        if User.objects.filter(username=telephone).exists():
            raise ValidationError("Un compte existe déjà avec ce numéro.")
        return telephone

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Les deux mots de passe ne correspondent pas.")
        if p1:
            try:
                validate_password(p1)
            except ValidationError as e:
                self.add_error('password1', e.messages[0])
        return cleaned

    def save(self):
        """Crée l'utilisateur + son profil Parent."""
        telephone = self.cleaned_data['telephone']
        password = self.cleaned_data['password1']
        user = User.objects.create_user(username=telephone, password=password)
        Parent.objects.get_or_create(user=user, defaults={'telephone': telephone})
        return user
