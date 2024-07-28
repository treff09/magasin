from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Categorie(models.Model):
    type_voiture = models.CharField(max_length=100)
    numero = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.type_voiture} - {self.numero}"

class Fournisseur(models.Model):
    nom = models.CharField(max_length=255)
    contact = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.nom

class Piece(models.Model):
    type_voiture = models.ForeignKey(Categorie, on_delete=models.CASCADE)
    numero_piece = models.CharField(max_length=100)
    designation = models.CharField(max_length=255)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    quantite = models.PositiveIntegerField()
    emplacement = models.CharField(max_length=255)
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.designation} - {self.numero_piece}"
