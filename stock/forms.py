from django import forms
from .models import Piece,Fournisseur
from django.forms import DateInput

class DateForm(forms.Form):
    date_debut = forms.DateField(widget=forms.DateInput(attrs={'type': 'date','class':'form-control'}))
    date_fin = forms.DateField(widget=forms.DateInput(attrs={'type': 'date','class':'form-control'}))

class PieceForm(forms.ModelForm):
    class Meta:
        model = Piece
        fields = ['type_voiture', 'numero_piece', 'designation', 'prix_unitaire','prix_achat', 'quantite', 'emplacement', 'fournisseur']
        widgets = {
            'type_voiture': forms.Select(attrs={'class':'form-control'}),
            'numero_piece': forms.TextInput(attrs={'class':'form-control',"placeholder":"000"}),
            'designation': forms.TextInput(attrs={'class':'form-control',"placeholder":"Frein....",}),
            'prix_achat': forms.NumberInput(attrs={'class':'form-control',"placeholder":"...0frscfa","min":0}),
            'prix_unitaire': forms.NumberInput(attrs={'class':'form-control',"placeholder":"...0frscfa","min":0}),
            'quantite': forms.NumberInput(attrs={'class':'form-control',"placeholder":"0",}),
            'emplacement': forms.TextInput(attrs={'class':'form-control',"placeholder":"E1 R1",}),
            'fournisseur': forms.Select(attrs={'class':'form-control',"placeholder":"Cfao...",}),
        }
        
class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'contact',]
        widgets = {
            'nom': forms.TextInput(attrs={'class':'form-control',"placeholder":"Nom"}),
            'contact': forms.TextInput(attrs={'class':'form-control',"placeholder":"(+)....",}),
        }
        
        
class AjouterAuPanierForm(forms.Form):
    pieces = forms.ModelMultipleChoiceField(queryset=Piece.objects.all(), widget=forms.CheckboxSelectMultiple)
    quantites = forms.CharField(widget=forms.HiddenInput)

