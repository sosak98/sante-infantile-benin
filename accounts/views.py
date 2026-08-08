from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import random
from datetime import timedelta

from .forms import PhoneSendForm, PhoneVerifyForm
from .models import Profile
from .models import PhoneOTP

@login_required
def dashboard(request):
    user = request.user

    # Récupérer prénom de façon robuste (User.first_name ou profile.first_name)
    first_name = (user.first_name or
                  getattr(getattr(user, 'profile', None), 'first_name', '') or
                  getattr(getattr(user, 'parent', None), 'first_name', '') or
                  '')

    # Heure locale
    now_local = timezone.localtime(timezone.now())
    hour = now_local.hour

    if 5 <= hour < 12:
        salutation = "Bonjour"
    elif 12 <= hour < 18:
        salutation = "Bon après-midi"
    else:
        salutation = "Bonsoir"

    if first_name:
        greeting = f"{salutation} {first_name}"
        show_profile_prompt = False
    else:
        greeting = "Bienvenue"
        show_profile_prompt = True

    # Récupération robuste de la liste d'enfants (différents related_name possibles)
    children_qs = None
    for rel in ('children', 'child_set', 'enfants', 'enfant_set'):
        rel_attr = getattr(user, rel, None)
        if rel_attr:
            try:
                # si c'est un manager QuerySet
                children_qs = rel_attr.all()
                break
            except Exception:
                # rel_attr peut être autre chose, on ignore
                children_qs = None

    children_count = children_qs.count() if children_qs is not None else 0
    children_sample = list(children_qs[:3]) if children_qs is not None else []

    context = {
        'greeting': greeting,
        'show_profile_prompt': show_profile_prompt,
        'children_count': children_count,
        'children_sample': children_sample,
    }
    return render(request, 'accounts/dashboard.html', context)


def about(request):
    return render(request, 'accounts/a_propos.html')


# --- OTP phone verification flow (prototype) ---
from django.views.decorators.http import require_http_methods
from .utils import send_sms

OTP_EXPIRY_MINUTES = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
OTP_MAX_ATTEMPTS = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)

@require_http_methods(['GET', 'POST'])
def send_phone_otp(request):
    """Affiche le formulaire pour envoyer un OTP par SMS et crée l'enregistrement OTP."""
    if request.method == 'POST':
        form = PhoneSendForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            # Générer code 6 chiffres
            code = f"{random.randint(0, 999999):06d}"
            user = request.user if request.user.is_authenticated else None
            # Marquer anciens codes non vérifiés comme expirés simplement en laissant l'ancien
            otp = PhoneOTP.objects.create(user=user, phone=phone, code=code)

            message = f"Votre code de vérification SIB est : {code} (valide {OTP_EXPIRY_MINUTES} min)."
            sent = send_sms(phone, message)

            # On ne révèle pas si l'envoi a échoué côté client
            messages.success(request, 'Un code de vérification a été envoyé si le numéro est valide.')
            return render(request, 'accounts/phone_verify_sent.html', {'phone': phone})
    else:
        form = PhoneSendForm()
    return render(request, 'accounts/phone_send.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def verify_phone_otp(request):
    """Vérifie le code OTP envoyé au numéro. Si OK, marque vérifié et associe au profil si connecté."""
    if request.method == 'POST':
        form = PhoneVerifyForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            code = form.cleaned_data['code'].strip()
            # chercher le dernier OTP pour ce numéro
            otp = PhoneOTP.objects.filter(phone=phone).order_by('-created_at').first()
            if not otp:
                messages.error(request, 'Aucun code envoyé pour ce numéro.')
                return redirect('accounts:phone_send')

            # vérifier expiration
            if timezone.now() > otp.created_at + timedelta(minutes=OTP_EXPIRY_MINUTES):
                messages.error(request, 'Le code a expiré. Demandez un nouveau code.')
                return redirect('accounts:phone_send')

            if otp.attempts >= OTP_MAX_ATTEMPTS:
                messages.error(request, 'Trop de tentatives. Demandez un nouveau code.')
                return redirect('accounts:phone_send')

            if otp.code == code:
                otp.verified = True
                otp.save()
                # associer au profil si connecté
                if request.user.is_authenticated:
                    profile, _ = Profile.objects.get_or_create(user=request.user)
                    profile.phone = phone
                    profile.save()
                messages.success(request, 'Numéro vérifié avec succès.')
                return render(request, 'accounts/phone_verify_success.html', {'phone': phone})
            else:
                otp.attempts += 1
                otp.save()
                messages.error(request, 'Code invalide. Réessayez.')
                return render(request, 'accounts/phone_verify.html', {'form': form, 'phone': phone})
    else:
        phone = request.GET.get('phone', '')
        form = PhoneVerifyForm(initial={'phone': phone})
    return render(request, 'accounts/phone_verify.html', {'form': form, 'phone': phone})
