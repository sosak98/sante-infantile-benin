from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ParentRegisterForm

def register(request):
    if request.method == 'POST':
        form = ParentRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé pour {username} ! Vous pouvez maintenant vous connecter.')
            return redirect('login')
    else:
        form = ParentRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})
