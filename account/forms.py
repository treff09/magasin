from django import forms
from django.contrib.auth.models import User
from .models import Profile

class UserForm(forms.ModelForm):
    
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"magasin@20",'class':'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Bradtref",'class':'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"........",'class':'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder":"email@gmail.com....",'class':'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder":"1234.....",'class':'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder":"1234.....",'class':'form-control'}))
    
    
   
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
       

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['role',]
        widgets = {
            'role': forms.Select(attrs={'class':'form-control'}),
        } 
