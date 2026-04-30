kkfrom django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ParentRegisterForm

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

def dashboard(request):
    return render(request, 'accounts/dashboard.html')
