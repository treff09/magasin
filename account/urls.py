from django.shortcuts import render
from django.urls import path
from .views import  ForgotPasswordView, PasswordChangeView, RequestEmailView, VerifyOtpView,OptValid,PasswordChangeDoneView, user_detail, user_create, user_update, user_delete
from .views import login_view,logout_view
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views

urlpatterns = [
    
    path('users/<int:pk>/', user_detail, name='user_detail'),
    path('users/new/', user_create, name='user_create'),
    path('users/<int:pk>/edit/', user_update, name='user_update'),
    path('users/<int:pk>/delete/', user_delete, name='user_delete'),
    
    # path('caissier_dashboard/', login_required(lambda request: render(request, 'caissier_dashboard.html')), name='caissier_dashboard'),
    # path('accueillant_dashboard/', login_required(lambda request: render(request, 'accueillant_dashboard.html')), name='accueillant_dashboard'),
    # path('livraison_dashboard/', login_required(lambda request: render(request, 'livraison_dashboard.html')), name='livraison_dashboard'),
    
    path('', login_view, name='login'),
    path('logout/', logout_view, name='deconnexion'),
    #mot de passe oublé 
      #les vue a renseigner
    path('forgotpass/', ForgotPasswordView.as_view(), name='forgot'),
    # path('otp/', opt.as_view(), name='opt'),
    path('otp/', OptValid.as_view(), name='otp'),

    #fonction phare
    path('request-email/', RequestEmailView.as_view(), name='request_email'),
    path('verify-otp/', VerifyOtpView.as_view(), name='verify_otp'),

     path('password_change/',PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),
    
]
