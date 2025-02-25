from datetime import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User,Group
from django.views import View

from magazin_piece import settings
from .models import Profile
from .forms import UserForm, ProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import PWD_FORGET
from django.core.mail import EmailMultiAlternatives

def is_admin_magasin(user):
    return user.is_authenticated and user.groups.filter(name='AdminMagasin').exists()
    
# @user_passes_test(is_admin_magasin)
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
            return redirect('caisseDashboard')
        elif user.groups.filter(name='Accueillants').exists():
            messages.success(request, "Bienvenue au service accueil")
            return redirect('piece')
        elif user.groups.filter(name='Livraisons').exists():
            messages.success(request, "Bienvenue au service livraison")
            return redirect('livraison')
        else:
            messages.success(request, "Bienvenue administrateur")
            return redirect('caiss') 
            # return redirect('adminmagasin') 
        
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.groups.filter(name='Caissiers').exists():
                    return redirect('caissier_dashboard')
                elif user.groups.filter(name='Accueillants').exists():
                    messages.success(request, "Bienvenue au service accueil")
                    return redirect('piece_list_accueil')
                elif user.groups.filter(name='Livraisons').exists():
                    messages.success(request, "Bienvenue au service livraison")
                    return redirect('livraison_dashboard')
                elif user.groups.filter(name='adminmagasin').exists():
                    messages.success(request, "Bienvenue administrateur")
                    return redirect('adminmagasin') 
                else:
                    return redirect('login')
            else:
                messages.error(request, f"Utilisateur ou mot de passe incorrecte")
        except:
            messages.error(request, "Information de connexion invalides!!!")
    return render(request, "perfect/logins.html")
    
def logout_view(request):
    logout(request)
    messages.success(request, "Vous êtes deconnecté.")
    return redirect("login")

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views import View
from .models import PWD_FORGET
from django.contrib.auth.models import User
import random
from django.utils import timezone

# Vue pour afficher le formulaire de saisie de l'email
class ForgotPasswordView(View):
    def get(self, request):
        return render(request, 'perfect/forgot_password.html')


# class opt(View):
#     def get(self, request):
#         return render(request, 'verify_otp.html')
# Vue pour traiter la demande de réinitialisation de mot de passe
class RequestEmailView(View):
    def post(self, request):
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = ''.join(random.choices('0123456789', k=4))
            PWD_FORGET.objects.create(user_id=user, otp=otp, status='0')

            subject = 'Votre OTP de réinitialisation de mot de passe'
            from_email = settings.EMAIL_HOST_USER
            to = [email]

            # HTML message
            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Réinitialisation du mot de passe</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="text-align: center; color: #333;">REINITIALISATION DE MOT DE PASSE</h2>
                    <p>Bonjour cher {user.username},</p>
                    <p>Vous avez demandé à réinitialiser votre mot de passe. Veuillez utiliser le code OTP ci-dessous pour compléter cette action :</p>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <p style="font-size: 20px; font-weight: bold; color: #2c3e50;">Votre code OTP : <span style="color: #e74c3c;">{otp}</span></p>
                    </div>
                    
                    <p style="color: #555;">Ce code est valable pour une durée limitée. Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet e-mail. Pour toute assistance, veuillez nous contacter immédiatement.</p>
            
                    <p>Merci de votre confiance.</p>
            
                    <p>Cordialement,<br>L'équipe support</p>
            
                    <footer style="margin-top: 20px; text-align: center; font-size: 12px; color: #999;">
                        &copy; 2024-2025 Bradi One. Tous droits réservés.
                    </footer>
                </div>
            </body>
            </html>
            '''
            # Create email message with HTML content
            email_message = EmailMultiAlternatives(subject, 'Votre OTP est {otp}', from_email, to)
            email_message.attach_alternative(html_content, 'text/html')
            email_message.send()

            return redirect("otp")
        except User.DoesNotExist:
            messages.error(request, "Utilisateur non trouvé.")
            return  render(request, "perfect/forgot_password.html")

# Vue pour vérifier l'OTP envoyé par email
User = get_user_model()

class VerifyOtpView(View):
    def get(self, request):
        return render(request, 'perfect/reinitialise.html')

    def post(self, request):
        otp = request.session.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not otp or not new_password or not confirm_password:
            return JsonResponse({'error': 'Tous les champs sont obligatoires.'}, status=400)

        if new_password != confirm_password:
            messages.error(request, "Mots de passe pas identique.")
            return  render(request, "perfect/reinitialise.html")

        try:
            reset_request = PWD_FORGET.objects.get(otp=otp, status='0')
            # Vérifiez si l'OTP a expiré
            if (timezone.now() - reset_request.creat_at).total_seconds() > 120:  # 2 minutes
                messages.error(request, "OTP expiré")
                return redirect('otp')
            # Marquer l'OTP comme utilisé
            reset_request.status = '1'
            reset_request.save()

            # Réinitialiser le mot de passe
            user = reset_request.user_id
            user.password = make_password(new_password)
            user.save()
            messages.success(request, 'Mot de passe réinitialisé avec succès.')
            return redirect('login')
        except PWD_FORGET.DoesNotExist:
            messages.error(request, 'OTP non valide.')
            return  render(request, "perfect/otp.html")

class OptValid(View):
    def get(self, request):
        return render(request, 'perfect/otp.html')
    def post(self, request):
        otp = request.POST.get('otp')
        try :
            reset_request = PWD_FORGET.objects.get(otp=otp, status='0')
            print(f"-----------------------------------")
            print(f"verification : {reset_request}")
            print(f"-----------------------------------")
            request.session['otp'] = otp
            if reset_request :
                return redirect("verify_otp")
        except PWD_FORGET.DoesNotExist:
                 messages.error(request, "OTP non valide.")
                 return  render(request, "perfect/otp.html")
               
from .forms import ChangePasswordForm
from django.contrib.auth.views import PasswordChangeView 
from django.urls import reverse_lazy
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin

class PasswordChangeView(PasswordChangeView):
    form_class = ChangePasswordForm
    template_name = 'change_password.html'
    success_message = "Mot de passe réinitialisé avec succès👍✓✓"
    error_message = "Erreur de saisie ���� ✘✘"
    success_url = reverse_lazy('password_change')
    def form_valid(self, form):
        reponse = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return reponse
    def form_invalid(self, form):
        reponse = super().form_invalid(form)
        messages.error(self.request, self.error_message)
        return reponse 
    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return render(request, self.template_name, {'form': form})
    
class PasswordChangeDoneView(View):
    def get(self, request):
         return render(request, 'password_change_done.html')
