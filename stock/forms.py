from django import forms
from .models import Piece

class PieceForm(forms.ModelForm):
    class Meta:
        model = Piece
        fields = ['type_voiture', 'numero_piece', 'designation', 'prix_unitaire', 'quantite', 'emplacement', 'fournisseur']
