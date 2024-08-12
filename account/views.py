from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User,Group
from .models import Profile
from .forms import UserForm, ProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def is_admin_magasin(user):
    return user.is_authenticated and user.groups.filter(name='AdminMagasin').exists()

@user_passes_test(is_admin_magasin)
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'profile.html', {'user': user})

login_required(login_url='login')
@user_passes_test(is_admin_magasin)
def user_create(request):
    users = User.objects.filter(is_superuser=False)
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            group = Group.objects.get(name=profile.role)
            user.groups.add(group)
            messages.success(request, 'Utilisateur enregistré avec succès')
            return redirect('user_create')
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
    return render(request, 'users_list.html', {'user_form': user_form,
                                               'profile_form': profile_form,
                                               'users': users
                                               })
login_required(login_url='login')
@user_passes_test(is_admin_magasin)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = get_object_or_404(Profile, user=user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            user.groups.clear()
            group = Group.objects.get(name=profile.role)
            user.groups.add(group)
            messages.success(request, 'Utilisateur modifié avec succès')
            return redirect('user_create')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    return render(request, 'users_list.html', {'user_form': user_form, 'profile_form': profile_form})

login_required(login_url='login')
@user_passes_test(is_admin_magasin)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request,f'le compte de {{user}} a été supprimer avec succès')
        return redirect('user_create')
    return render(request, 'user_confirm_delete.html', {'user': user})

def login_view(request):
    if request.user.is_authenticated:
        user = request.user
        if user.groups.filter(name='Caissiers').exists():
            return redirect('caissier_accueil')
        elif user.groups.filter(name='Accueillants').exists():
            messages.success(request, "Bienvenue au service accueil")
            return redirect('piece')
        elif user.groups.filter(name='Livraisons').exists():
            messages.success(request, "Bienvenue au service livraison")
            return redirect('livraison')
        else:
            messages.success(request, "Bienvenue administrateur")
            return redirect('adminmagasin')  
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.groups.filter(name='Caissiers').exists():
                return redirect('caissier_dashboard')
            elif user.groups.filter(name='Accueillants').exists():
                messages.success(request, "Bienvenue au service accueil")
                return redirect('accueillant_dashboard')
            elif user.groups.filter(name='Livraisons').exists():
                messages.success(request, "Bienvenue au service livraison")
                return redirect('livraison_dashboard')
            else:
                messages.success(request, "Bienvenue administrateur")
                return redirect('adminmagasin')  
        else:
            return render(request, 'logins.html', {'error': 'Nom utilisateur ou mot de passe incorrecte'})
    else:
        return render(request, 'logins.html')
    
    
    
def logout_view(request):
    logout(request)
    messages.success(request, "Vous êtes deconnecté.")
    return redirect("login")



