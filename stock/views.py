from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from .models import Categorie, Piece, Fournisseur, Panier, PanierItem, Commande, Ticket
from .forms import AjouterAuPanierForm, PieceForm
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string


def base(request):
    return render(request,'magasin/base.html',)
login_required(login_url='login')
def admin_magasin(request):
    return render(request,'dash_admin_magasin.html',)


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
    # Retrieve or create the cart for the current user
    panier, created = Panier.objects.get_or_create(utilisateur=request.user, valide=False)
    panier_items = PanierItem.objects.filter(panier=panier)

    # Calculate totals
    for item in panier_items:
        item.total = item.piece.prix_unitaire * item.quantite
    sous_total = sum(item.total for item in panier_items)

    context = {
        'pieces': pieces,
        'panier_items': panier_items,
        'sous_total': sous_total,
    }
    return render(request, 'piece_list.html', context)
@user_passes_test(is_accueillant)
def ajouter_au_panier(request, piece_id):
    piece = get_object_or_404(Piece, id=piece_id)
    panier, created = Panier.objects.get_or_create(utilisateur=request.user, valide=False)
    panier_item, created = PanierItem.objects.get_or_create(panier=panier, piece=piece)
    # Increment quantity if item already exists in the cart
    if not created:
        panier_item.quantite += 1
        panier_item.save()
    return redirect('piece_list_accueil')

def retirer_du_cart(request, piece_id):
    # Récupérer la pièce et l'élément du panier correspondant
    piece = get_object_or_404(Piece, id=piece_id)
    panier = get_object_or_404(Panier, utilisateur=request.user, valide=False)
    panier_item = get_object_or_404(PanierItem, panier=panier, piece=piece)

    # Réduire la quantité ou supprimer l'article si la quantité est 1
    if panier_item.quantite > 1:
        panier_item.quantite -= 1
        panier_item.save()
    else:
        panier_item.delete()
    return redirect('piece_list_accueil')

from decimal import Decimal, InvalidOperation# Redirect to the page showing both list and cart
@user_passes_test(is_accueillant)
def valider_panier(request):
    panier = get_object_or_404(Panier, utilisateur=request.user, valide=False)
    # Calculer le total du panier
    total = sum(item.piece.prix_unitaire * item.quantite for item in PanierItem.objects.filter(panier=panier))
    # Créer une nouvelle commande pour le panier
    remise = request.POST.get('remise')
    
    # if remise is not None:
    try:
        remise = Decimal(remise) if remise else Decimal('0')
    except (ValueError, InvalidOperation):
        remise = Decimal('0')
        
    if remise > 0:
        remise = Decimal(remise)
        montant_remise = (remise / Decimal('100')) * total
        total_apres_remise = total - montant_remise
        print("remise",remise, "---------", montant_remise,"T=",total ,"----aprm-----", total_apres_remise)
    else:
        total_apres_remise = total
        print("---------", "---------", total_apres_remise)
        
    # Créer une nouvelle commande pour le panier
    commande = Commande.objects.create(
        panier=panier,
        numero_commande='CMD' + str(panier.id) + '-' + str(Commande.objects.filter(panier=panier).count() + 1),
        total=total_apres_remise,
        utilisateur=request.user,
        remise=remise,
        total_sans_remise=total
    )
    print('')
    print('---------commande-----------',commande.numero_commande,commande.total)
    print('')
    # Créer un ticket pour la nouvelle commande
    ticket = Ticket.objects.create(
        numero='TKT' + str(commande.id),
        commande=commande
    )
    
    # Vider le panier
    #PanierItem.objects.filter(panier=panier).delete()
    
    # Marquer le panier comme validé
    panier.valide = True
    numero=f"TKT{str(commande.id)}"
    numero=str(numero)
    panier.ticket =numero
    panier.save()

    messages.success(request, f"Panier validé avec succès. Votre numéro de ticket est {ticket.numero}.")
    return redirect('piece_list_accueil')


@user_passes_test(is_accueillant)
def supprimer_du_panier(request, item_id):
    panier = Panier.objects.get(utilisateur=request.user, valide=False)
    panier_item = get_object_or_404(PanierItem, id=item_id, panier=panier)
    # Remove item from the cart
    panier_item.delete()
    return redirect('piece_list_accueil')

@user_passes_test(is_admin_magasin)
def piece_detail(request, pk):
    piece = get_object_or_404(Piece, pk=pk)
    return render(request, 'piece_detail.html', {'piece': piece})

@user_passes_test(is_admin_magasin)
def piece_create(request):
    stock = Piece.objects.all()
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
            return redirect('piece_create')
    else:
        form = PieceForm()
    return render(request, 'create_piece.html', {'form': form, 'stocks': stock})

@user_passes_test(is_admin_magasin)
def piece_update(request, pk):
    piece = get_object_or_404(Piece, pk=pk)
    if request.method == 'POST':
        form = PieceForm(request.POST, instance=piece)
        if form.is_valid():
            form.save()
            messages.success(request, f"La pièce {piece.numero_piece} a été mise à jour.")
            return redirect('piece_create')
    else:
        form = PieceForm(instance=piece)
    return render(request, 'create_piece.html', {'form': form})


@user_passes_test(is_admin_magasin)
def piece_delete(request, pk):
    piece = get_object_or_404(Piece, pk=pk)
    if request.method == 'POST':
        piece.delete()
        messages.success(request, f"La pièce {piece.numero_piece} a été supprimée.")
        return redirect('piece_create')
    return render(request, 'create_piece.html', {'piece': piece})

    # return render(request, 'piece_confirm_delete.html', {'piece': piece})

from django.db import transaction
@user_passes_test(is_accueillant)
def panier(request):
    panier, created = Panier.objects.get_or_create(utilisateur=request.user, valide=False)
    
    if created:
        # Si un nouveau panier est créé, aucun panier_item existant n'est associé
        panier_items = []
    else:
        # Sinon, nous obtenons les items associés au panier existant
        panier_items = PanierItem.objects.filter(panier=panier)

    # Calculer les totaux
    for item in panier_items:
        item.total = item.piece.prix_unitaire * item.quantite
    sous_total = sum(item.total for item in panier_items)

    if request.method == 'POST':
        for item in panier_items:
            quantite = int(request.POST.get(f'quantite_{item.piece.id}', 0))
            item.quantite = quantite
            item.save()
        remise = request.POST.get('remise', 0)
        panier.valide = True
        panier.save()
        return redirect('piece_list') 
    context = {
        'panier_items': panier_items,
        'panier': panier,
        'sous_total': sous_total,
    }
    return render(request, 'panier.html', context)



@user_passes_test(is_caissier)
def valider_paiement(request, ticket_id):
    paniers_non_valides = Panier.objects.filter(valide=True,panier_paye = False)
    ticket = get_object_or_404(Ticket, numero=ticket_id, utilise=False)
    commande = ticket.commande
    panier = commande.panier
    if request.method == 'POST':
        montant = request.POST.get('montant')
        
        if float(montant) >= commande.total:
            commande.paye = True
            reste = float(montant) - float(commande.total)
            commande.utilisateur = request.user
            commande.montant_paye=float(montant)
            commande.montant_reste= abs(reste)
            commande.paye
            commande.save()
            ticket.utilise = True
            ticket.utilisateur = request.user
            ticket.save()
            panier.panier_paye=True
            panier.save()
            # Mettre à jour le stock
            for item in PanierItem.objects.filter(panier=panier):
                piece = item.piece
                piece.quantite -= item.quantite
                piece.save()
            messages.success(request, f"Paiement validé. Utilisez le numéro {ticket.numero} pour récupérer vos articles.")
            return redirect('caisseDashboard')
        
        else:
            messages.error(request, "Le montant payé ne correspond pas au total de la commande.")
    # Passer les items du panier au template
    panier_items = PanierItem.objects.filter(panier=panier)
    context = {
        'ticket': ticket,
        'commande': commande,
        'paniers_non_valides': paniers_non_valides,
        'panier_items': panier_items,
    }
    print(commande.panier,'\n')
    return render(request, 'caissiere_validation_paiement.html', context)

# @user_passes_test(is_caissier)
# def caissier_accueil(request):
#     return render(request, 'caissier_accueil.html')

@user_passes_test(is_liveur)
def valider_livraison(request, ticket_id):
    ticket = get_object_or_404(Ticket, numero=ticket_id, utilise=True)
    
    if request.method == 'POST':
        panier_non_livre = Panier.objects.filter(ticket=ticket.numero).first()
        panier_non_livre.panier_livre = True
        panier_non_livre.save()
        messages.success(request, f"Livraison validée pour le ticket {ticket.numero}.")
        return redirect('livraison_dashboard')
    return render(request, 'valider_livraison.html', {'ticket': ticket})

@user_passes_test(is_liveur)
def livraison_accueil(request):
    return render(request, 'livraison_accueil.html')

@user_passes_test(is_accueillant)
def accueil(request):
    return render(request, 'accueil.html')

@user_passes_test(is_caissier)
def caisseDashboard(request):
    paniers_non_valides = Panier.objects.filter(valide=True,panier_paye = False,panier_livre=False)
    context =  {
        'paniers_non_valides': paniers_non_valides,
    }
    return render(request, 'caissiere_validation_paiement.html', context)


@user_passes_test(is_liveur)
def livraison_dashboard(request):
    # Filtrer les paniers dont le statut 'valide' est True
    livraison_en_attente = Panier.objects.filter(valide=True,panier_paye = True,panier_livre=False) 
    return render(request, 'livraison.html', {'livraison_en_attente': livraison_en_attente})


import qrcode
import io
import base64
from django.shortcuts import render, get_object_or_404
from .models import Commande, PanierItem

def generate_receipt(request, commande_id):
    # Récupérer la commande basée sur l'ID
    commande = get_object_or_404(Commande, id=commande_id)

    # Calculer le montant restant (s'il n'est pas déjà calculé)
    if commande.total and commande.montant_paye:
        commande.montant_reste = commande.montant_paye - commande.total 

    # Récupérer les pièces dans le panier de la commande
    panier = commande.panier
    panier_items = PanierItem.objects.filter(panier=panier)

    # Générer un QR code avec une taille réduite
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,  # Réduit la taille des pixels du QR code
        border=2,    # Réduit la largeur de la bordure
    )
    qr_data = f"Commande #{commande.numero_commande} - Total: {commande.total} Fcfa - Date : {commande.date_creation}"
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Convertir le QR code en image et l'encoder en base64
    img = qr.make_image(fill='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Rendre la page du reçu avec QR code et détails des pièces
    return render(request, 'reçu.html', {
        'commande': commande,
        'qr_code_img': img_str,
        'panier_items': panier_items
    })
