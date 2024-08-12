from django import forms
from .models import Piece

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

