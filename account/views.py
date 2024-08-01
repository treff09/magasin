from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User,Group
from .models import Profile
from .forms import UserForm, ProfileForm
from django.contrib.auth import authenticate, login

def is_admin_magasin(user):
    return user.groups.filter(name='AdminMagasin').exists()

@user_passes_test(is_admin_magasin)
def user_list(request):
    users = User.objects.filter(is_superuser=False)
    return render(request, 'user_list.html', {'users': users})

@user_passes_test(is_admin_magasin)
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'user_detail.html', {'user': user})

@user_passes_test(is_admin_magasin)
def user_create(request):
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
            return redirect('user_list')
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
    return render(request, 'user_form.html', {'user_form': user_form, 'profile_form': profile_form})

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
            return redirect('user_list')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    return render(request, 'user_form.html', {'user_form': user_form, 'profile_form': profile_form})

@user_passes_test(is_admin_magasin)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('user_list')
    return render(request, 'user_confirm_delete.html', {'user': user})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.groups.filter(name='Caissiers').exists():
                return redirect('caissier_dashboard')
            elif user.groups.filter(name='Accueillants').exists():
                return redirect('accueillant_dashboard')
            elif user.groups.filter(name='Livraisons').exists():
                return redirect('livraison_dashboard')
            else:
                return redirect('user_list')  
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    else:
        return render(request, 'login.html')