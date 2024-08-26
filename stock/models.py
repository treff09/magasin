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

class Panier(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paniers')
    valide = models.BooleanField(default=False)
    panier_paye = models.BooleanField(default=False)
    # date_creation = models.DateTimeField(auto_now_add=True)
    ticket = models.CharField(max_length=100, null=True, blank=True)
    panier_livre = models.BooleanField(default=False)

class PanierItem(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE,related_name='panier_items')
    piece = models.ForeignKey(Piece, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)


class Commande(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='commands')
    numero_commande = models.CharField(max_length=100)
    total_sans_remise = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)# Nouveau champ pour la remise
    date_creation = models.DateTimeField(auto_now_add=True)
    paye = models.BooleanField(default=False)
    montant_paye=models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    montant_reste=models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
<<<<<<< HEAD
    remise = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
=======
    remise =models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
>>>>>>> a75edca57c091ff6bf37ea1ed2c247e79d686911
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commandes_validees', null=True, blank=True)

class Ticket(models.Model):
    numero = models.CharField(max_length=100)
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    utilise = models.BooleanField(default=False)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='livraisons_effectuees', null=True, blank=True)

