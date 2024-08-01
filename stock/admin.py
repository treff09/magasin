from django.contrib import admin
from .models import Categorie, Piece, Fournisseur,PanierItem

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['type_voiture', 'numero']
    search_fields = ['type_voiture', 'numero']

@admin.register(Piece)
class PieceAdmin(admin.ModelAdmin):
    list_display = ['type_voiture', 'numero_piece', 'designation', 'prix_unitaire', 'quantite', 'emplacement', 'utilisateur', 'fournisseur']
    search_fields = ['type_voiture__type_voiture', 'numero_piece', 'designation']
    list_filter = ['type_voiture']

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ['nom', 'contact']
    search_fields = ['nom']

@admin.register(PanierItem)
class PanierItemAdmin(admin.ModelAdmin):
    list_display = ['panier', 'piece','quantite']
    search_fields = ['piece']