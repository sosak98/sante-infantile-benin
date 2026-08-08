from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required

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
