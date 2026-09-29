"""Formulaires de l'espace professionnels de santé."""

from django import forms
from django.contrib.auth.models import User

from sante.models import CODES_JOURS, JOURS_SEMAINE, Etablissement

from .models import ProfessionnelSante


class InscriptionProForm(forms.Form):
    """Demande de compte professionnel (soumise à validation)."""

    prenom = forms.CharField(max_length=100, label='Prénom')
    nom = forms.CharField(max_length=100, label='Nom')
    email = forms.EmailField(label='Adresse e-mail professionnelle')
    telephone = forms.CharField(max_length=20, label='Téléphone')
    fonction = forms.ChoiceField(choices=ProfessionnelSante.FONCTIONS, label='Fonction')
    numero_ordre = forms.CharField(
        max_length=50, required=False, label="Numéro d'ordre ou matricule",
        help_text="Facilite la validation de votre compte.",
    )
    etablissement = forms.ModelChoiceField(
        queryset=Etablissement.objects.none(), required=False,
        label='Formation sanitaire',
        help_text="Laissez vide si votre structure n'est pas dans la liste.",
    )
    structure_libre = forms.CharField(
        max_length=200, required=False, label='Autre structure',
    )
    mot_de_passe = forms.CharField(
        widget=forms.PasswordInput, min_length=8, label='Mot de passe',
        help_text='8 caractères minimum.',
    )
    mot_de_passe2 = forms.CharField(
        widget=forms.PasswordInput, label='Confirmez le mot de passe',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Seules les structures qui peuvent vacciner sont proposées.
        self.fields['etablissement'].queryset = Etablissement.objects.exclude(
            type_etab='pharmacie'
        ).order_by('nom')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Un compte existe déjà avec cette adresse.')
        return email

    def clean(self):
        donnees = super().clean()
        if donnees.get('mot_de_passe') != donnees.get('mot_de_passe2'):
            self.add_error('mot_de_passe2', 'Les deux mots de passe diffèrent.')
        if not donnees.get('etablissement') and not donnees.get('structure_libre'):
            self.add_error(
                'structure_libre',
                'Indiquez votre structure, ou choisissez-la dans la liste.',
            )
        return donnees

    def save(self):
        donnees = self.cleaned_data
        user = User.objects.create_user(
            username=donnees['email'],
            email=donnees['email'],
            password=donnees['mot_de_passe'],
            first_name=donnees['prenom'],
            last_name=donnees['nom'],
        )
        return ProfessionnelSante.objects.create(
            user=user,
            fonction=donnees['fonction'],
            etablissement=donnees.get('etablissement'),
            structure_libre=donnees.get('structure_libre', ''),
            numero_ordre=donnees.get('numero_ordre', ''),
            telephone=donnees['telephone'],
        )


class JoursVaccinationForm(forms.ModelForm):
    """Déclaration des jours de vaccination d'un centre, par son agent."""

    jours = forms.MultipleChoiceField(
        choices=JOURS_SEMAINE,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Jours de séance de vaccination',
    )

    class Meta:
        model = Etablissement
        fields = [
            'fait_vaccination', 'horaire_vaccination',
            'precision_vaccination', 'telephone', 'commune',
        ]
        labels = {
            'fait_vaccination': 'Ce centre organise des séances de vaccination PEV',
            'telephone': 'Téléphone du centre',
            'commune': 'Commune',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['jours'].initial = self.instance.jours_liste

    def clean(self):
        donnees = super().clean()
        jours = [j for j in donnees.get('jours', []) if j in CODES_JOURS]
        if donnees.get('fait_vaccination') and not jours:
            self.add_error(
                'jours',
                'Cochez au moins un jour, sinon décochez « organise des séances ».',
            )
        donnees['jours'] = jours
        return donnees

    def save(self, commit=True, source='centre'):
        from django.utils import timezone

        etablissement = super().save(commit=False)
        jours = self.cleaned_data.get('jours', [])
        etablissement.jours_vaccination = ','.join(jours)
        if jours:
            etablissement.source_vaccination = source
            etablissement.maj_vaccination = timezone.now()
        else:
            etablissement.source_vaccination = ''
            etablissement.maj_vaccination = None
        if commit:
            etablissement.save()
        return etablissement
