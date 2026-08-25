from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_http_methods
import random
from datetime import timedelta, date

from .forms import ParentRegisterForm, PhoneSendForm, PhoneVerifyForm
from .models import Parent, Profile, PhoneOTP
from .utils import send_sms
from enfants.models import Enfant, VaccinRecu
from conseils.pev import planifier

OTP_EXPIRY_MINUTES = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
OTP_MAX_ATTEMPTS = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)


# ---------------------------------------------------------------------------
# Page d'accueil
# ---------------------------------------------------------------------------
def accueil(request):
    return render(request, 'accounts/accueil.html')


def about(request):
    return render(request, 'accounts/a_propos.html')


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------
def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    if request.method == 'POST':
        form = ParentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, 'Compte créé avec succès. Bienvenue sur Santé Infantile Bénin !')
            return redirect('accounts:dashboard')
    else:
        form = ParentRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url or 'accounts:dashboard')
    else:
        form = AuthenticationForm(request)
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    messages.info(request, 'Vous êtes déconnecté. À bientôt !')
    return redirect('accounts:accueil')


# ---------------------------------------------------------------------------
# Espace parent
# ---------------------------------------------------------------------------
@login_required
def dashboard(request):
    user = request.user
    parent = getattr(user, 'parent', None)
    children = Enfant.objects.filter(parent=parent) if parent else Enfant.objects.none()

    prenom = ''
    if parent:
        prenom = parent.prenom or user.first_name or ''
    greeting = f"Bienvenue, {prenom}".strip() if prenom else "Bienvenue"

    recus = VaccinRecu.objects.filter(enfant__in=children).count()
    a_venir = 0
    today = date.today()
    for enfant in children:
        recus_map = {
            v.nom_vaccin: v.date_reelle
            for v in VaccinRecu.objects.filter(enfant=enfant)
        }
        for ligne in planifier(enfant.date_naissance, recus_map, today):
            if ligne['statut'] in ('A venir', "Aujourd_hui", 'En retard'):
                a_venir += 1

    context = {
        'greeting': greeting,
        'parent': parent,
        'children_count': children.count(),
        'children_sample': list(children[:3]),
        'vaccins_recus_count': recus,
        'vaccins_a_venir_count': a_venir,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profil(request):
    """Affichage + mise à jour du profil parent."""
    parent = getattr(request.user, 'parent', None)
    if parent is None:
        parent = Parent.objects.create(user=request.user)

    if request.method == 'POST':
        parent.prenom = request.POST.get('prenom', '').strip()
        parent.nom = request.POST.get('nom', '').strip()
        parent.quartier = request.POST.get('quartier', '').strip()
        parent.ville = request.POST.get('ville', '').strip()
        if request.FILES.get('photo'):
            parent.photo = request.FILES['photo']
        parent.save()
        messages.success(request, 'Profil mis à jour avec succès.')
        return redirect('accounts:profil')

    enfants = Enfant.objects.filter(parent=parent)
    return render(request, 'accounts/profil.html', {'parent': parent, 'enfants': enfants})


# Alias conservé pour les liens existants
profile_edit = profil


@login_required
def ajouter_enfant(request):
    parent = getattr(request.user, 'parent', None)
    if parent is None:
        parent = Parent.objects.create(user=request.user)

    if request.method == 'POST':
        prenom = request.POST.get('prenom', '').strip()
        nom = request.POST.get('nom', '').strip()
        date_naissance = request.POST.get('date_naissance')
        sexe = request.POST.get('sexe', 'M')

        if prenom and nom and date_naissance:
            try:
                d = date.fromisoformat(date_naissance)
                Enfant.objects.create(
                    parent=parent, prenom=prenom, nom=nom,
                    date_naissance=d, sexe=sexe,
                )
                messages.success(request, f'{prenom} a été ajouté avec succès.')
                return redirect('accounts:profil')
            except ValueError:
                messages.error(request, 'Date de naissance invalide.')
        else:
            messages.error(request, 'Veuillez remplir tous les champs obligatoires.')

    return render(request, 'accounts/ajouter_enfant.html', {'parent': parent})


# ---------------------------------------------------------------------------
# Vérification OTP par téléphone (prototype)
# ---------------------------------------------------------------------------
@require_http_methods(['GET', 'POST'])
def send_phone_otp(request):
    if request.method == 'POST':
        form = PhoneSendForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            code = f"{random.randint(0, 999999):06d}"
            user = request.user if request.user.is_authenticated else None
            PhoneOTP.objects.create(user=user, phone=phone, code=code)

            message = f"Votre code de vérification SIB est : {code} (valide {OTP_EXPIRY_MINUTES} min)."
            send_sms(phone, message)

            messages.success(request, 'Un code de vérification a été envoyé si le numéro est valide.')
            return render(request, 'accounts/phone_verify_sent.html', {'phone': phone})
    else:
        form = PhoneSendForm()
    return render(request, 'accounts/phone_send.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def verify_phone_otp(request):
    if request.method == 'POST':
        form = PhoneVerifyForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            code = form.cleaned_data['code'].strip()
            otp = PhoneOTP.objects.filter(phone=phone).order_by('-created_at').first()

            if not otp:
                messages.error(request, 'Aucun code envoyé pour ce numéro.')
                return redirect('accounts:phone_send')

            if timezone.now() > otp.created_at + timedelta(minutes=OTP_EXPIRY_MINUTES):
                messages.error(request, 'Le code a expiré. Demandez un nouveau code.')
                return redirect('accounts:phone_send')

            if otp.attempts >= OTP_MAX_ATTEMPTS:
                messages.error(request, 'Trop de tentatives. Demandez un nouveau code.')
                return redirect('accounts:phone_send')

            if otp.code == code:
                otp.verified = True
                otp.save()
                if request.user.is_authenticated:
                    parent, _ = Parent.objects.get_or_create(user=request.user)
                    parent.telephone = phone
                    parent.save()
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
