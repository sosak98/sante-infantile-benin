from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ParentRegisterForm
from .models import Parent
from enfants.models import Enfant

def accueil(request):
    return render(request, 'accounts/accueil.html')

def register(request):
    if request.method == 'POST':
        form = ParentRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Compte créé avec succès ! Connectez-vous.')
            return redirect('login')
    else:
        form = ParentRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def dashboard(request):
    parent = Parent.objects.get(user=request.user)
    return render(request, 'accounts/dashboard.html', {'parent': parent})

@login_required
def profil(request):
    parent = Parent.objects.get(user=request.user)
    enfants = Enfant.objects.filter(parent=parent)

    if request.method == 'POST':
        parent.nom = request.POST.get('nom', '')
        parent.prenom = request.POST.get('prenom', '')
        parent.quartier = request.POST.get('quartier', '')
        parent.ville = request.POST.get('ville', 'Cotonou')
        if request.FILES.get('photo'):
            parent.photo = request.FILES['photo']
        parent.save()
        messages.success(request, 'Profil mis à jour avec succès !')
        return redirect('profil')

    return render(request, 'accounts/profil.html', {
        'parent': parent,
        'enfants': enfants,
    })

@login_required
def ajouter_enfant(request):
    parent = Parent.objects.get(user=request.user)
    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        date_naissance = request.POST.get('date_naissance')
        sexe = request.POST.get('sexe')
        Enfant.objects.create(
            parent=parent,
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            sexe=sexe
        )
        messages.success(request, f'Enfant {prenom} ajouté avec succès !')
        return redirect('profil')
    return render(request, 'accounts/ajouter_enfant.html')
