"""Espace professionnels de santé.

Trois niveaux d'accès, volontairement distincts :

1. anonyme            -> présentation + demande de compte
2. compte non validé  -> page d'attente uniquement
3. compte validé      -> tableau de bord, fiche du centre, outils PEV

Le décorateur `pro_valide_requis` garantit qu'aucune vue métier n'est
accessible avant validation du compte.
"""

from datetime import date
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render

from conseils.pev import (
    CALENDRIER_PEV,
    age_en_mois,
    calendrier_affichable,
    planifier,
    resume_couverture,
)
from sante.models import CODES_JOURS, LIBELLES_JOURS, Etablissement, code_du_jour

from .forms import InscriptionProForm, JoursVaccinationForm
from .models import ProfessionnelSante


INSCRIPTION_PRO_MAX_POSTS = 5
INSCRIPTION_PRO_RATE_LIMIT_SECONDS = 15 * 60


def profil_pro(request):
    """Le profil professionnel de l'utilisateur courant, ou None."""
    if not request.user.is_authenticated:
        return None
    return getattr(request.user, 'professionnel', None)


def pro_valide_requis(vue):
    """Réserve une vue aux comptes professionnels validés."""

    @wraps(vue)
    @login_required
    def _enveloppe(request, *args, **kwargs):
        pro = profil_pro(request)
        if pro is None:
            messages.warning(
                request, "Cet espace est réservé aux professionnels de santé."
            )
            return redirect('pro:accueil')
        if not pro.est_valide:
            return redirect('pro:en_attente')
        return vue(request, *args, **kwargs)

    return _enveloppe


# ---------------------------------------------------------------------------
# Accès public
# ---------------------------------------------------------------------------
def accueil(request):
    """Présentation de l'espace + point d'entrée vers la demande de compte."""
    pro = profil_pro(request)
    if pro and pro.est_valide:
        return redirect('pro:tableau_de_bord')
    centres_publies = Etablissement.objects.filter(
        fait_vaccination=True,
    ).exclude(jours_vaccination='').count()
    return render(request, 'pro/accueil.html', {
        'pro': pro,
        'centres_publies': centres_publies,
        'nb_doses': len(CALENDRIER_PEV),
    })


def inscription(request):
    if request.user.is_authenticated and profil_pro(request):
        return redirect('pro:accueil')

    if request.method == 'POST':
        ip_client = request.META.get('REMOTE_ADDR', '') or 'inconnu'
        cle_limite = f"pro_inscription:{ip_client}"
        tentatives = cache.get(cle_limite, 0)
        form = InscriptionProForm(request.POST)
        if tentatives >= INSCRIPTION_PRO_MAX_POSTS:
            form.add_error(
                None,
                "Trop de demandes depuis cette connexion. Réessayez dans 15 minutes.",
            )
        else:
            cache.set(
                cle_limite,
                tentatives + 1,
                timeout=INSCRIPTION_PRO_RATE_LIMIT_SECONDS,
            )
            if form.is_valid():
                pro = form.save()
                auth_login(request, pro.user)
                messages.success(
                    request,
                    "Demande enregistrée. Votre compte sera actif dès validation "
                    "par l'équipe.",
                )
                return redirect('pro:en_attente')
    else:
        form = InscriptionProForm()
    return render(request, 'pro/inscription.html', {'form': form})


@login_required
def en_attente(request):
    pro = profil_pro(request)
    if pro is None:
        return redirect('pro:accueil')
    if pro.est_valide:
        return redirect('pro:tableau_de_bord')
    return render(request, 'pro/en_attente.html', {'pro': pro})


# ---------------------------------------------------------------------------
# Espace validé
# ---------------------------------------------------------------------------
@pro_valide_requis
def tableau_de_bord(request):
    pro = profil_pro(request)
    etablissement = pro.etablissement
    jour = code_du_jour()
    return render(request, 'pro/tableau_de_bord.html', {
        'pro': pro,
        'etablissement': etablissement,
        'seance_aujourd_hui': etablissement.vaccine_aujourd_hui() if etablissement else None,
        'jour_libelle': LIBELLES_JOURS[jour],
        'calendrier': calendrier_affichable(),
    })


@pro_valide_requis
def fiche_centre(request):
    """Déclaration des jours de vaccination du centre de l'agent."""
    pro = profil_pro(request)
    if pro.etablissement is None:
        messages.warning(
            request,
            "Aucune formation sanitaire n'est rattachée à votre compte. "
            "Contactez l'équipe pour la rattacher.",
        )
        return redirect('pro:tableau_de_bord')

    etablissement = pro.etablissement
    if request.method == 'POST':
        form = JoursVaccinationForm(request.POST, instance=etablissement)
        if form.is_valid():
            form.save(source='centre')
            messages.success(
                request,
                "Jours de vaccination mis à jour : ils sont visibles "
                "immédiatement par les parents.",
            )
            return redirect('pro:fiche_centre')
    else:
        form = JoursVaccinationForm(instance=etablissement)

    return render(request, 'pro/fiche_centre.html', {
        'pro': pro,
        'form': form,
        'etablissement': etablissement,
    })


@pro_valide_requis
def outil_pev(request):
    """Planificateur PEV rapide : une date de naissance, un planning.

    Pensé pour la consultation : l'agent n'a pas à créer de compte parent
    pour répondre à « quand dois-je revenir ? ».
    """
    planning = None
    resume = None
    age_mois = None
    naissance = None
    erreur = None

    if request.method == 'POST':
        brut = request.POST.get('date_naissance') or ''
        try:
            naissance = date.fromisoformat(brut)
        except ValueError:
            erreur = "Date de naissance invalide."
        else:
            if naissance > date.today():
                erreur = "La date de naissance ne peut pas être dans le futur."
                naissance = None
            else:
                # Les doses cochées sont réputées reçues à leur date théorique.
                connues = {entree['cle'] for entree in CALENDRIER_PEV}
                deja = set(request.POST.getlist('recu')) & connues
                theorique = planifier(naissance, {})
                recus = {
                    ligne['cle']: ligne['date_prevue']
                    for ligne in theorique if ligne['cle'] in deja
                }
                planning = planifier(naissance, recus)
                resume = resume_couverture(naissance, recus)
                age_mois = age_en_mois(naissance)

    return render(request, 'pro/outil_pev.html', {
        'planning': planning,
        'resume': resume,
        'age_mois': age_mois,
        'naissance': naissance,
        'erreur': erreur,
        'calendrier': CALENDRIER_PEV,
    })
