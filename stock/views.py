from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from .models import Categorie, Piece, Fournisseur, Panier, PanierItem, Commande, Ticket
from .forms import AjouterAuPanierForm, PieceForm
from django.contrib import messages 

def is_admin_magasin(user):
    return user.groups.filter(name='AdminMagasin').exists()
def is_caissier(user):
    return user.groups.filter(name__in=['Caissiers', 'AdminMagasin']).exists()
def is_accueillant(user):
    return user.groups.filter(name__in=['Accueillants', 'AdminMagasin']).exists()

def is_liveur(user):
    return user.groups.filter(name__in=['Livraisons', 'AdminMagasin']).exists()

@user_passes_test(is_accueillant)
def piece_list(request):
    pieces = Piece.objects.all()
    return render(request, 'piece_list.html', {'pieces': pieces})

@user_passes_test(is_admin_magasin)
def piece_detail(request, pk):
    piece = get_object_or_404(Piece, pk=pk)
    return render(request, 'piece_detail.html', {'piece': piece})

@user_passes_test(is_admin_magasin)
def piece_create(request):
    if request.method == 'POST':
        form = PieceForm(request.POST)
        if form.is_valid():
            numero_piece = form.cleaned_data['numero_piece']
            type_voiture = form.cleaned_data['type_voiture']
            quantite = form.cleaned_data['quantite']
            try:
                piece = Piece.objects.get(numero_piece=numero_piece,type_voiture=type_voiture)
                piece.quantite += quantite
                piece.save()
                messages.success(request, f"La quantité de la pièce {numero_piece} a été mise à jour.")
            except Piece.DoesNotExist:
                piece = form.save(commit=False)
                piece.utilisateur = request.user
                piece.save()
                messages.success(request, f"La pièce {numero_piece} a été ajoutée.")
            return redirect('piece_list')
    else:
        form = PieceForm()
    return render(request, 'piece_form.html', {'form': form})

@user_passes_test(is_admin_magasin)
def piece_update(request, pk):
    piece = get_object_or_404(Piece, pk=pk)
    if request.method == 'POST':
        form = PieceForm(request.POST, instance=piece)
        if form.is_valid():
            form.save()
            messages.success(request, f"La pièce {piece.numero_piece} a été mise à jour.")
            return redirect('piece_list')
    else:
        form = PieceForm(instance=piece)
    return render(request, 'piece_form.html', {'form': form})

@user_passes_test(is_admin_magasin)
def piece_delete(request, pk):
    piece = get_object_or_404(Piece, pk=pk)
    if request.method == 'POST':
        piece.delete()
        messages.success(request, f"La pièce {piece.numero_piece} a été supprimée.")
        return redirect('piece_list')
    return render(request, 'piece_confirm_delete.html', {'piece': piece})





@user_passes_test(is_accueillant)
def ajouter_au_panier(request):
    if request.method == 'POST':
        panier, created = Panier.objects.get_or_create(utilisateur=request.user, valide=False)
        
        # Itérer à travers chaque pièce
        for key in request.POST:
            if key.startswith('quantites_'):
                piece_id = key.replace('quantites_', '')
                quantite = int(request.POST.get(key, 0))
                
                if quantite > 0:
                    piece = get_object_or_404(Piece, pk=piece_id)
                    panier_item, created = PanierItem.objects.get_or_create(panier=panier, piece=piece)
                    
                    if not created:
                        panier_item.quantite += quantite
                    else:
                        panier_item.quantite = quantite
                    panier_item.save()
        
        messages.success(request, "Les articles ont été ajoutés au panier.")
        return redirect('panier_detail')
    
    return redirect('piece_list')



@user_passes_test(is_accueillant) 
def panier_detail(request):
    panier = get_object_or_404(Panier, utilisateur=request.user, valide=False)
    items = PanierItem.objects.filter(panier=panier)
    return render(request, 'panier_detail.html', {'panier': panier, 'items': items})

@user_passes_test(is_accueillant)
def valider_panier(request):
    panier = get_object_or_404(Panier, utilisateur=request.user, valide=False)
    
    # Calculer le total du panier
    total = sum(item.piece.prix_unitaire * item.quantite for item in PanierItem.objects.filter(panier=panier))
    
    # Créer une nouvelle commande pour le panier
    commande = Commande.objects.create(
        panier=panier,
        numero_commande='CMD' + str(panier.id) + '-' + str(Commande.objects.filter(panier=panier).count() + 1),
        total=total,
        utilisateur=request.user
    )
    
    # Créer un ticket pour la nouvelle commande
    ticket = Ticket.objects.create(
        numero='TKT' + str(commande.id),
        commande=commande
    )
    
    # Vider le panier
    PanierItem.objects.filter(panier=panier).delete()
    
    # Marquer le panier comme validé
    panier.valide = True
    numero=f"TKT{str(commande.id)}"
    numero=str(numero)
    panier.ticket =numero
    panier.save()

    messages.success(request, f"Panier validé avec succès. Votre numéro de ticket est {ticket.numero}.")
    return redirect('accueil')

@user_passes_test(is_caissier)
def valider_paiement(request, ticket_id):
    ticket = get_object_or_404(Ticket, numero=ticket_id, utilise=False)
    commande = ticket.commande
    panier = commande.panier
    
    if request.method == 'POST':
        montant = request.POST.get('montant')
        if float(montant) == commande.total:
            commande.paye = True
            commande.utilisateur = request.user
            commande.save()
            ticket.utilise = True
            ticket.save()
            
            # Mettre à jour le stock
            for item in PanierItem.objects.filter(panier=panier):
                piece = item.piece
                piece.quantite -= item.quantite
                piece.save()
            
            messages.success(request, f"Paiement validé. Utilisez le numéro {ticket.numero} pour récupérer vos articles.")
            return redirect('caissier_accueil')
        else:
            messages.error(request, "Le montant payé ne correspond pas au total de la commande.")
    
    return render(request, 'valider_paiement.html', {'ticket': ticket, 'commande': commande})

@user_passes_test(is_caissier)
def caissier_accueil(request):
    return render(request, 'caissier_accueil.html')

@user_passes_test(is_caissier)
def valider_livraison(request, ticket_id):
    ticket = get_object_or_404(Ticket, numero=ticket_id, utilise=True)
    if request.method == 'POST':
        ticket.utilisateur = request.user
        ticket.save()
        messages.success(request, f"Livraison validée pour le ticket {ticket.numero}.")
        return redirect('livraison_accueil')
    
    return render(request, 'valider_livraison.html', {'ticket': ticket})

@user_passes_test(is_liveur)
def livraison_accueil(request):
    return render(request, 'livraison_accueil.html')

@user_passes_test(is_accueillant)
def accueil(request):
    return render(request, 'accueil.html')



def caisse_dashboard(request):
    # Filtrer les paniers dont le statut 'valide' est False
    paniers_en_attente = Panier.objects.filter(valide=True) and Ticket.objects.filter(utilise=False) 
    return render(request, 'caissier_dashboard.html', {'paniers_en_attente': paniers_en_attente})