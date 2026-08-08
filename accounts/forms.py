from django import forms

class PhoneSendForm(forms.Form):
    phone = forms.CharField(max_length=20, label="Numéro de téléphone",
                            widget=forms.TextInput(attrs={'placeholder': '+229XXXXXXXX'}))

class PhoneVerifyForm(forms.Form):
    phone = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(max_length=6, label="Code reçu", widget=forms.TextInput(attrs={'placeholder': '123456'}))
