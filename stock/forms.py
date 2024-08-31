from django import forms
from .models import Piece
from django.forms import DateInput

class DateForm(forms.Form):
    date_debut = forms.DateField(widget=forms.DateInput(attrs={'type': 'date','class':'form-control'}))
    date_fin = forms.DateField(widget=forms.DateInput(attrs={'type': 'date','class':'form-control'}))
class PieceForm(forms.ModelForm):
    class Meta:
        model = Piece
        fields = ['type_voiture', 'numero_piece', 'designation', 'prix_unitaire', 'quantite', 'emplacement', 'fournisseur']
        widgets = {
            'type_voiture': forms.Select(attrs={'class':'form-control'}),
            
            'numero_piece': forms.TextInput(attrs={'class':'form-control',"placeholder":"000"}),
            'designation': forms.TextInput(attrs={'class':'form-control',"placeholder":"Frein....",}),
            'prix_unitaire': forms.NumberInput(attrs={'class':'form-control',"placeholder":"...0frscfa",}),
            'quantite': forms.NumberInput(attrs={'class':'form-control',"placeholder":"0",}),
            'emplacement': forms.TextInput(attrs={'class':'form-control',"placeholder":"E1 R1",}),
            
            'fournisseur': forms.Select(attrs={'class':'form-control',"placeholder":"Cfao...",}),
        }
        
        
class AjouterAuPanierForm(forms.Form):
    pieces = forms.ModelMultipleChoiceField(queryset=Piece.objects.all(), widget=forms.CheckboxSelectMultiple)
    quantites = forms.CharField(widget=forms.HiddenInput)



# class RemiseForm(forms.Form):
#     remise = forms.DecimalField(
#         max_digits=5, 
#         decimal_places=2, 
#         min_value=0, 
#         max_value=100,
#         label="Remise (%)",
#         widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Entrez la remise en %'})
#     )





