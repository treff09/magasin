import calendar
from datetime import date, datetime, timedelta, timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy
from .models import Categorie, Piece, Fournisseur, Panier, PanierItem, Commande, Ticket
from .forms import AjouterAuPanierForm, PieceForm, DateForm, FournisseurForm
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper, Q
from django.views.generic import ListView, DetailView,CreateView, DeleteView, UpdateView, TemplateView
from django.db.models.functions import TruncMonth
from django.db.models.functions import ExtractMonth


def raci(request):
    return render(request,'perfect/tableau_bord.html',)
def caisse(request):
    return render(request,'perfect/caisse.html',)

def base(request):
    return render(request,'magasin/base.html',)
login_required(login_url='login')

class DashboardView(TemplateView):
    template_name = 'dashboard.html'
    form_class = DateForm
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_group = self.request.user.groups.first()
        context['user_group'] = user_group.name if user_group else None
        mois_en_cours=date.today().month
        libelle_mois_en_cours = calendar.month_name[mois_en_cours]
        form = self.form_class(self.request.GET)
        if form.is_valid():
            date_debut = form.cleaned_data['date_debut'] 
            date_fin = form.cleaned_data['date_fin'] 

             # AFFICHAGE DES DONNEES DU JOUR EN COURS
            total_pieces = Piece.objects.aggregate(total=Sum('quantite'))['total'] or 0
            # Total inventaire
            total_inventaire = Piece.objects.aggregate(total_value=Sum(ExpressionWrapper(F('prix_unitaire') * F('quantite'), output_field=DecimalField())))['total_value'] or 0
            # Total Commandes
            nb_cmd_jour = Commande.objects.filter(panier__valide=True, date_creation=date.today()).count()
            print("~~~~~~~~~~cmd_jours~~~~~~~~~~~~~~~~~~~~~~", nb_cmd_jour)

            total_cmde_revenue_jour = Commande.objects.filter(paye=True, date_creation=date.today()).aggregate(total=Sum('total'))['total'] or 0
            total_cmde_mois_en_cours = Commande.objects.filter(paye=True, date_creation__range=[date_debut, date_fin]).aggregate(total=Sum('total'))['total'] or 0
            total_cmde_annee_en_cours = Commande.objects.filter(paye=True, date_creation__year=date.today().year).aggregate(total=Sum('total'))['total'] or 0
            nb_cmde_annee_en_cours = Commande.objects.filter(paye=True, date_creation__year=date.today().year).count()
            nb_cmde_mois_en_cours = Commande.objects.filter(paye=True, date_creation__range=[date_debut, date_fin]).count()
            # Commandes payee livrer
            cmd_payee_livrer = Commande.objects.filter(paye=True, panier__panier_livre=True,date_creation__range=[date_debut, date_fin]).count()
            # Commandes en attente de paiement
            cmd_en_attente_jour = Commande.objects.filter(paye=False, date_creation__range=[date_debut, date_fin]).count()

            nb_piece_jour_vendu = PanierItem.objects.filter(
                panier__commands__isnull=False,  # On filtre pour les paniers qui sont liés à des commandes
                panier__valide=True,             # Panier validé
                panier__panier_paye=True,
                date_creation__range=[date_debut, date_fin]
            ).aggregate(total_pieces=Sum('quantite'))['total_pieces'] or 0

            nb_piece_mois_encours_vendu = PanierItem.objects.filter(panier__valide=True,         
                                            panier__panier_paye=True,
                                            date_creation__range=[date_debut, date_fin]).count()
            
            nb_piece_annee_en_cours_vendu = PanierItem.objects.filter(panier__valide=True,         
                                            panier__panier_paye=True,
                                            date_creation__year=date.today().year).count()
            
            nb_paniers_jours_cours = Panier.objects.filter(date_creation=date.today()).count()
            nb_paniers_mois_cours = Panier.objects.filter(date_creation__range=[date_debut, date_fin]).count()
            nb_paniers_anneen_cours = Panier.objects.filter(date_creation__year=date.today().year).count()
            
            validated_paniers = Panier.objects.filter(valide=True, panier_paye=False, date_creation__range=[date_debut, date_fin]).count()
            
            # Nombre de tickets émis et utilisés
            total_tickets_issued = Ticket.objects.filter(commande__panier__valide=True,commande__panier__panier_paye=False, date_creation__range=[date_debut, date_fin]).count()
            print("Total tickets issued", total_tickets_issued)
            total_tickets_used = Ticket.objects.filter(utilise=True, date_creation__range=[date_debut, date_fin]).count()
            # Commandes entièrement payées et livrées
            
            # Pièces dont le stock est faible
            low_stock_pieces = Piece.objects.filter(quantite__lte=5,date_creation__range=[date_debut, date_fin]).count()

            #estimat_stock = (total_pieces/total_paniers)
            #if total_paniers == 0:
            #    estimat_stock = 0
            #estimat_stock_format = '{:.2f}'.format(estimat_stock)
            # Paniers that are validated but not yet paid
            #----------------------------------------------------------------------------#
            #pieces_by_category_alto = Piece.objects.filter(type_voiture__type_voiture__in=['ALTO']).count()
            #pieces_by_category_dzire = Piece.objects.filter(type_voiture__type_voiture__in=['DZIRE']).count()
            #pieces_by_category_swift = Piece.objects.filter(type_voiture__type_voiture__in=['SWIFT']).count()
            #total_inventory_restant = total_inventory_value - total_revenue_mois
    
            #Le Detail des quantités par type de voitures
            total_quantite_alto = Piece.objects.filter(type_voiture__type_voiture='ALTO',date_creation__range=[date_debut, date_fin]).aggregate(total_quantite=Sum('quantite'))['total_quantite'] or 0
            total_quantite_dzire = Piece.objects.filter(type_voiture__type_voiture='DZIRE',date_creation__range=[date_debut, date_fin]).aggregate(total_quantite=Sum('quantite'))['total_quantite'] or 0
            total_quantite_swift = Piece.objects.filter(type_voiture__type_voiture='SWIFT',date_creation__range=[date_debut, date_fin]).aggregate(total_quantite=Sum('quantite'))['total_quantite'] or 0
            # Total des pièces pour les commandes dont les pièces sont pour les voitures de type DZIRE,ALTO,SWIFT
            
            total_pieces_swift = PanierItem.objects.filter(piece__type_voiture__type_voiture='SWIFT',
                panier__commands__isnull=False,  # On filtre pour les paniers qui sont liés à des commandes
                panier__valide=True,             # Panier validé
                panier__panier_paye=True,
                date_creation__range=[date_debut, date_fin]
            ).aggregate(total_pieces=Sum('quantite'))['total_pieces'] or 0
    
            total_pieces_alto = PanierItem.objects.filter(
                piece__type_voiture__type_voiture='ALTO',
                panier__valide=True, panier__panier_paye=True,
                panier__commands__isnull=False,
                date_creation__range=[date_debut, date_fin]
            ).aggregate(total_pieces=Sum('quantite'))['total_pieces'] or 0
    
            total_pieces_dzire = PanierItem.objects.filter(
                piece__type_voiture__type_voiture='DZIRE',
                panier__valide=True, panier__panier_paye=True,
                panier__commands__isnull=False,
                date_creation__range=[date_debut, date_fin]
            ).aggregate(total_pieces=Sum('quantite'))['total_pieces'] or 0
            #--------------------------------------Graphs--------------------------------#
            total_revenue_filtre = PanierItem.objects.filter(panier__valide=True, 
                                                            panier__panier_paye=True,
                                                            date_creation__range=[date_debut, date_fin]
                                                            )
            
            revenue_mensuelle_filtre = {month: 0 for month in range(1, 13)}
            for commande in total_revenue_filtre:
                revenue_mensuelle_filtre[commande.date_creation.month] += 1
            revenue_mensuelle_data = [revenue_mensuelle_filtre[month] for month in range(1, 13)]
            labels = [calendar.month_name[month][:2] for month in range(1, 13)]
    
            top_categories = (
                PanierItem.objects.filter(piece__type_voiture__type_voiture__in=['SWIFT', 'ALTO', 'DZIRE'],
                                            panier__valide=True,         
                                            panier__panier_paye=True,
                                            date_creation__range=[date_debut, date_fin]
                                        )
                .values('piece__type_voiture__type_voiture')
                .annotate(
                    total_pieces=Sum('quantite'),
                    total_revenue=Sum(
                        ExpressionWrapper(F('piece__prix_unitaire') * F('quantite'), output_field=DecimalField())
                    )).order_by('-total_pieces')[:3])
    
            #Les pièces les plus vendues
            top_pieces = (
                PanierItem.objects.filter(date_creation__range=[date_debut, date_fin],
                                          panier__valide=True,         
                                          panier__panier_paye=True,)
                .values('piece__designation', 'piece__type_voiture__type_voiture')  
                .annotate(total_commandes=Count('id'), total_somme=Sum(
                        ExpressionWrapper(F('piece__prix_unitaire') * F('quantite'), output_field=DecimalField())
                    )).order_by('-total_commandes')[:3])
            
            total_cms_unpaid = Commande.objects.filter(date_creation__month=date.today().month,).aggregate(total=Sum('montant_reste'))['total'] or 0
            # best_pieces = sorted([x for x in best_pieces if x['recs'] is not None], key=lambda x: x['recs'], reverse=True)[:10]
        else:
            # AFFICHAGE DES DONNEES DU JOUR EN COURS
            total_pieces = Piece.objects.aggregate(total=Sum('quantite'))['total'] or 0
            # Total inventaire
            total_inventaire = Piece.objects.aggregate(total_value=Sum(ExpressionWrapper(F('prix_unitaire') * F('quantite'), output_field=DecimalField())))['total_value'] or 0
            # Total Commandes
            nb_cmd_jour = Commande.objects.filter(panier__valide=True, date_creation=date.today()).count()
            print("~~~~~~~~~~cmd_jours~~~~~~~~~~~~~~~~~~~~~~", nb_cmd_jour)

            total_cmde_revenue_jour = Commande.objects.filter(paye=True, date_creation=date.today()).aggregate(total=Sum('total'))['total'] or 0
            total_cmde_mois_en_cours = Commande.objects.filter(paye=True, date_creation__year=date.today().year, date_creation__month=date.today().month).aggregate(total=Sum('total'))['total'] or 0
            total_cmde_annee_en_cours = Commande.objects.filter(paye=True, date_creation__year=date.today().year).aggregate(total=Sum('total'))['total'] or 0
            nb_cmde_annee_en_cours = Commande.objects.filter(paye=True, date_creation__year=date.today().year).count()
            nb_cmde_mois_en_cours = Commande.objects.filter(paye=True, date_creation__year=date.today().year, date_creation__month=date.today().month).count()
            # Commandes payee livrer
            cmd_payee_livrer = Commande.objects.filter(paye=True, panier__panier_livre=True,date_creation=date.today(),).count()
            # Commandes en attente de paiement
            cmd_en_attente_jour = Commande.objects.filter(paye=False, date_creation=date.today()).count()

            nb_piece_jour_vendu = PanierItem.objects.filter(
                panier__commands__isnull=False,  
                panier__valide=True,             
                panier__panier_paye=True,
                date_creation=date.today()
            ).aggregate(total_pieces=Sum('quantite'))['total_pieces'] or 0

            nb_piece_mois_encours_vendu = PanierItem.objects.filter(panier__valide=True,         
                                            panier__panier_paye=True,
                                            date_creation__year=date.today().year, 
                                            date_creation__month=date.today().month).count()
            
            nb_piece_annee_en_cours_vendu = PanierItem.objects.filter(panier__valide=True,         
                                            panier__panier_paye=True,
                                            date_creation__year=date.today().year).count()
            
            nb_paniers_jours_cours = Panier.objects.filter(date_creation=date.today()).count()
            nb_paniers_mois_cours = Panier.objects.filter(date_creation__year=date.today().year, date_creation__month=date.today().month).count()
            nb_paniers_anneen_cours = Panier.objects.filter(date_creation__year=date.today().year).count()
            
            validated_paniers = Panier.objects.filter(valide=True, panier_paye=False, date_creation=date.today()).count()
            
            # Nombre de tickets émis et utilisés
            total_tickets_issued = Ticket.objects.filter(commande__panier__valide=True,commande__panier__panier_paye=False, date_creation=date.today()).count()
            print("Total tickets issued", total_tickets_issued)
            total_tickets_used = Ticket.objects.filter(utilise=True, date_creation=date.today()).count()
            # Commandes entièrement payées et livrées
            
            # Pièces dont le stock est faible
            low_stock_pieces = Piece.objects.filter(quantite__lte=5).count()

            #estimat_stock = (total_pieces/total_paniers)
            #if total_paniers == 0:
            #    estimat_stock = 0
            #estimat_stock_format = '{:.2f}'.format(estimat_stock)
            # Paniers that are validated but not yet paid
            #----------------------------------------------------------------------------#
            #pieces_by_category_alto = Piece.objects.filter(type_voiture__type_voiture__in=['ALTO']).count()
            #pieces_by_category_dzire = Piece.objects.filter(type_voiture__type_voiture__in=['DZIRE']).count()
            #pieces_by_category_swift = Piece.objects.filter(type_voiture__type_voiture__in=['SWIFT']).count()
            #total_inventory_restant = total_inventory_value - total_revenue_mois
    
            #Le Detail des quantités par type de voitures
            total_quantite_alto = Piece.objects.filter(type_voiture__type_voiture='ALTO').aggregate(total_quantite=Sum('quantite'))['total_quantite'] or 0
            total_quantite_dzire = Piece.objects.filter(type_voiture__type_voiture='DZIRE').aggregate(total_quantite=Sum('quantite'))['total_quantite'] or 0
            total_quantite_swift = Piece.objects.filter(type_voiture__type_voiture='SWIFT').aggregate(total_quantite=Sum('quantite'))['total_quantite'] or 0
            # Total des pièces pour les commandes dont les pièces sont pour les voitures de type DZIRE
            # Total des pièces pour les commandes dont les pièces sont pour les voitures de type ALTO
            # Total des pièces pour les commandes dont les pièces sont pour les voitures de type SWIFT
            total_pieces_swift = PanierItem.objects.filter(piece__type_voiture__type_voiture='SWIFT',
                panier__commands__isnull=False,  # On filtre pour les paniers qui sont liés à des commandes
                panier__valide=True,             # Panier validé
                panier__panier_paye=True,
                date_creation=date.today()
            ).aggregate(total_pieces=Sum('quantite'))['total_pieces'] or 0
    
            total_pieces_alto = PanierItem.objects.filter(
                piece__type_voiture__type_voiture='ALTO',
                panier__valide=True,             # Panier validé
                panier__panier_paye=True,
                panier__commands__isnull=False,date_creation=date.today()
            ).aggregate(total_pieces=Sum('quantite'))['total_pieces'] or 0
    
            total_pieces_dzire = PanierItem.objects.filter(
                piece__type_voiture__type_voiture='DZIRE',
                panier__valide=True,             # Panier validé
                panier__panier_paye=True,
                panier__commands__isnull=False,
                date_creation=date.today()
            ).aggregate(total_pieces=Sum('quantite'))['total_pieces'] or 0
    
            #--------------------------------------Graphs--------------------------------#
    
            total_revenue_filtre = PanierItem.objects.filter(panier__valide=True, 
                                                            panier__panier_paye=True,
                                                            date_creation__year=datetime.now().year)
            revenue_mensuelle_filtre = {month: 0 for month in range(1, 13)}
            for commande in total_revenue_filtre:
                revenue_mensuelle_filtre[commande.date_creation.month] += 1
            revenue_mensuelle_data = [revenue_mensuelle_filtre[month] for month in range(1, 13)]
            labels = [calendar.month_name[month][:2] for month in range(1, 13)]
            
            # total_cmde_mois_en_cours = Commande.objects.filter(paye=True, date_creation__year=date.today().year, date_creation__month=date.today().month).aggregate(total=Sum('total'))['total'] or 0
            # Valeur mensuelle des ventes
            val_mensuelle_filtre = {month: 0 for month in range(1, 13)}
            valeur_mens_cmde = Commande.objects.filter(paye=True, date_creation__year=datetime.now().year)

            for commande in valeur_mens_cmde:
                val_mensuelle_filtre[commande.date_creation.month] += float(commande.total)

            valeur_mensuelle_data = [val_mensuelle_filtre[month] for month in range(1, 13)]

            print(valeur_mensuelle_data,"-------*----------", revenue_mensuelle_data)
            
            top_categories = (
                PanierItem.objects.filter(piece__type_voiture__type_voiture__in=['SWIFT', 'ALTO', 'DZIRE'],
                                            panier__valide=True,         
                                            panier__panier_paye=True,
                                            date_creation=date.today()
                                        )
                .values('piece__type_voiture__type_voiture')
                .annotate(
                    total_pieces=Sum('quantite'),
                    total_revenue=Sum(
                        ExpressionWrapper(F('piece__prix_unitaire') * F('quantite'), output_field=DecimalField())
                    )).order_by('-total_pieces')[:3])
    
            #Les pièces les plus vendues
            top_pieces = (
                PanierItem.objects.filter(date_creation__month=date.today().month,
                                          panier__valide=True,         
                                          panier__panier_paye=True,)
                .values('piece__designation', 'piece__type_voiture__type_voiture')  
                .annotate(total_commandes=Count('id'), total_somme=Sum(
                        ExpressionWrapper(F('piece__prix_unitaire') * F('quantite'), output_field=DecimalField())
                    )).order_by('-total_commandes')[:3])
            
            total_cms_unpaid = Commande.objects.filter(date_creation__month=date.today().month,).aggregate(total=Sum('montant_reste'))['total'] or 0
            # best_pieces = sorted([x for x in best_pieces if x['recs'] is not None], key=lambda x: x['recs'], reverse=True)[:10]
            print(total_cms_unpaid)
            
            print("*********",labels, "***********",valeur_mensuelle_data)  

        context = {
        'libelle_mois_en_cours': libelle_mois_en_cours,

        'form': form,
        'top_pieces': top_pieces,
        'top_categories': top_categories,

        'total_pieces_alto': total_pieces_alto,
        'total_pieces_swift': total_pieces_swift,
        'total_pieces_dzire': total_pieces_dzire,
        #Total en stock
        'total_quantite_alto': total_quantite_alto,
        'total_quantite_dzire': total_quantite_dzire,
        'total_quantite_swift': total_quantite_swift,

        'revenue_mensuelle_data': revenue_mensuelle_data,
        'valeur_mensuelle_data': valeur_mensuelle_data,
        'labels': labels,
        'total_pieces': total_pieces,
        'total_inventaire': total_inventaire,
        #'total_orders': total_orders,
        'total_cmde_revenue_jour': total_cmde_revenue_jour,
        # 'total_unpaid': total_unpaid,
        # 'total_unpaid_jour': total_unpaid_jour,
        # 'total_unpaid_mois': total_unpaid_mois,
        'total_tickets_issued': total_tickets_issued,
        'total_tickets_used': total_tickets_used,
        #'fully_paid_delivered_orders': fully_paid_delivered_orders,
        #'pending_payment_orders': pending_payment_orders,
        'low_stock_pieces': low_stock_pieces,
        # 'total_paniers': total_paniers,
        'cmd_en_attente_jour': cmd_en_attente_jour,
        'cmd_payee_livrer': cmd_payee_livrer,
        # 'total_paniers': total_paniers,

        'nb_piece_jour_vendu': nb_piece_jour_vendu,
        'nb_cmde_mois_en_cours': nb_cmde_mois_en_cours,
        'nb_cmd_jour': nb_cmd_jour,
        'total_cmde_mois_en_cours': total_cmde_mois_en_cours,
        'nb_piece_mois_encours_vendu': nb_piece_mois_encours_vendu,
        'total_cmde_annee_en_cours': total_cmde_annee_en_cours,
        'nb_cmde_annee_en_cours': nb_cmde_annee_en_cours,
        'nb_piece_annee_en_cours_vendu': nb_piece_annee_en_cours_vendu,

        'validated_paniers': validated_paniers,
        
        'cmd_payee_livrer': cmd_payee_livrer,
        'nb_paniers_jours_cours': nb_paniers_jours_cours,
        'nb_paniers_mois_cours': nb_paniers_mois_cours,
        'nb_paniers_anneen_cours': nb_paniers_anneen_cours,
        #'estimat_stock_format': estimat_stock_format,
        }
        return context
      

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
    user = request.user
    role = None
    if hasattr(user, 'profile'):
        role = user.profile.role
    form = DateForm(request.GET)
    if form.is_valid():
        date_debut = form.cleaned_data['date_debut']
        date_fin = form.cleaned_data['date_fin']

        total_revenue_jour = Commande.objects.filter(utilisateur=user, date_creation__range=[date_debut, date_fin]).aggregate(total=Sum('total'))['total'] or 0
        if role in ['AdminMagasin', 'superadmin']:
            paniers = Panier.objects.filter(valide=True,date_creation__range=[date_debut, date_fin])
        else:
            # Show only paniers related to the connected user
            paniers = Panier.objects.filter(utilisateur=user, valide=True, date_creation__range=[date_debut, date_fin])
        
        total_pieces = Piece.objects.aggregate(total=Sum('quantite'))['total'] or 0
        total_inventory_value = Piece.objects.aggregate(total_value=Sum(ExpressionWrapper(F('prix_unitaire') * F('quantite'), output_field=DecimalField())))['total_value'] or 0

        panier_valide = PanierItem.objects.filter(panier__in=paniers, date_creation__range=[date_debut, date_fin]).count()
        command_valide = Commande.objects.filter(panier__in=paniers, date_creation__range=[date_debut, date_fin]).count()
        print(total_revenue_jour,"-------------------------",panier_valide,"-------------------------",command_valide)

        pieces = Piece.objects.filter(quantite__gt=0)
        # Retrieve or create the cart for the current user
        panier, created = Panier.objects.get_or_create(utilisateur=request.user, valide=False)
        
        panier_items = PanierItem.objects.filter(panier=panier)
        for item in panier_items:
            item.total = item.piece.prix_unitaire * item.quantite
        sous_total = sum(item.total for item in panier_items)
        total_revenue_mois = Commande.objects.filter(utilisateur=user, date_creation__year=date.today().year, date_creation__month=date.today().month).aggregate(total=Sum('total'))['total'] or 0
        nb_command_valide_mois = Commande.objects.filter(utilisateur=user, date_creation__year=date.today().year, date_creation__month=date.today().month).count()
        nb_panier_mensuelle_valide = PanierItem.objects.filter(panier__utilisateur=user, date_creation__year=date.today().year, date_creation__month=date.today().month).count()
        
    else:
        
        # Check if the user is a superadmin or adminMagasin
        if role in ['AdminMagasin', 'superadmin']:
            # Show all panier instances
            paniers = Panier.objects.filter(valide=True, date_creation=date.today())
        else:
            # Show only paniers related to the connected user
            paniers = Panier.objects.filter(utilisateur=user, valide=True, date_creation=date.today())
        
        total_pieces = Piece.objects.aggregate(total=Sum('quantite'))['total'] or 0
        panier_valide = PanierItem.objects.filter(panier__in=paniers).count()
        nb_panier_mensuelle_valide = PanierItem.objects.filter(panier__utilisateur=user, date_creation__year=date.today().year, date_creation__month=date.today().month).count()
        total_inventory_value = Piece.objects.aggregate(total_value=Sum(ExpressionWrapper(F('prix_unitaire') * F('quantite'), output_field=DecimalField())))['total_value'] or 0

        command_valide = Commande.objects.filter(utilisateur=user, panier__in=paniers, date_creation=date.today()).count()

        total_revenue_jour = Commande.objects.filter(utilisateur=user, date_creation=date.today()).aggregate(total=Sum('total'))['total'] or 0
        total_revenue_mois = Commande.objects.filter(utilisateur=user, date_creation__year=date.today().year, date_creation__month=date.today().month).aggregate(total=Sum('total'))['total'] or 0
        
        nb_command_valide_mois = Commande.objects.filter(utilisateur=user, date_creation__year=date.today().year, date_creation__month=date.today().month).count()
        print(nb_command_valide_mois)

        panier_items = PanierItem.objects.filter(panier__in=paniers)
        pieces = Piece.objects.filter(quantite__gt=0)
        # Retrieve or create the cart for the current user
        panier, created = Panier.objects.get_or_create(utilisateur=request.user, valide=False)
        panier_items = PanierItem.objects.filter(panier=panier)
        # Calculate totals
        for item in panier_items:
            item.total = item.piece.prix_unitaire * item.quantite
        sous_total = sum(item.total for item in panier_items)

    context = {
        'total_pieces': total_pieces,
        'total_inventory_value': total_inventory_value,
        'pieces': pieces,
        'total_revenue_jour': total_revenue_jour,
        'panier_items': panier_items,
        'sous_total': sous_total,
        'form': form,
        'total_revenue_mois': total_revenue_mois or 0,
        'panier_valide': panier_valide or 0,
        'command_valide': command_valide or 0,
        'nb_command_valide_mois': nb_command_valide_mois,
        'nb_panier_mensuelle_valide': nb_panier_mensuelle_valide,
        # 'nb_commands_valid': nb_commands_valid or 0,
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
# @user_passes_test(is_accueillant)
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
        numero_commande='CMD' + '-' +str(panier.id) + '-' + str(Commande.objects.filter(panier=panier).count() + 1),
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
    # Marquer le panier comme validé
    panier.valide = True
    numero=f"TKT{str(commande.id)}"
    numero=str(numero)
    panier.ticket =numero
    panier.save()
    messages.success(request, f"Panier validé avec succès. Votre numéro de ticket est {ticket.numero}.")
    return redirect('piece_list_accueil')


# @user_passes_test(is_accueillant)
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

# @user_passes_test(is_admin_magasin)
class AddfournisseurView(CreateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'create_fournisseur.html'
    success_message = 'Fournisseur enregistré avec succès👍✓✓'
    error_message = "Erreur de saisie ✘✘ "
    success_url = reverse_lazy ('fournisseur')
    def form_valid(self, form):
        reponse =  super().form_valid(form)
        messages.success(self.request, self.success_message)
        return reponse
    def form_invalid(self, form):
        reponse =  super().form_invalid(form)
        messages.success(self.request, self.error_message)
        return reponse
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_group = self.request.user.groups.first()
        context['user_group'] = user_group.name if user_group else None
        context['fournisseurs'] = Fournisseur.objects.all()
        return context
    
class UpdatefournisseurView(UpdateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'modifi_fournisseur.html'
    success_message = 'Modification effectuée avec succès👍✓✓'
    error_message = "Erreur de saisie ✘✘ "
    success_url = reverse_lazy ('fournisseur')
    def form_valid(self, form):
        reponse =  super().form_valid(form)
        messages.success(self.request, self.success_message)
        return reponse
    def form_invalid(self, form):
        reponse =  super().form_invalid(form)
        messages.success(self.request, self.error_message)
        return reponse
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_group = self.request.user.groups.first()
        context['user_group'] = user_group.name if user_group else None
        context['fournisseurs'] = Fournisseur.objects.all()
        return context

class DeletFournisseurView(DeleteView):
    model = Fournisseur
    template_name = 'delet_fournisseur.html' 
    success_message = 'Fournisseur Supprimé avec succès👍✓✓'
    success_url =reverse_lazy ('fournisseur')
    def form_valid(self, form):
        reponse =  super().form_valid(form)
        messages.success(self.request, self.success_message)
        return reponse
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_group = self.request.user.groups.first()
        context['user_group'] =user_group.name if user_group else None
        return context 

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
    return render(request, 'piece_modifi.html', {'form': form})


# @user_passes_test(is_admin_magasin)
def piece_delete(request, pk):
    piece = get_object_or_404(Piece, pk=pk)
    if request.method == 'POST':
        piece.delete()
        messages.success(request, f"La pièce {piece.numero_piece} a été supprimée.")
        return redirect('piece_create')
    return render(request, 'piece_delete.html', {'piece': piece})

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


from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import user_passes_test
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import qrcode
from PIL import Image
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
def generate_receipt_pdf(commande, panier_items, ticket):
    # Définir les dimensions du reçu en 57mm x 80mm
    width, height = 200 * 1, 420 * 1

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(width, height))
    y = height - 30
    
    logo_path = os.path.join(BASE_DIR,'static', 'icn.png')
    if os.path.exists(logo_path):
        logo_width, logo_height = 25, 25  # Taille du logo plus visible
        pdf.drawInlineImage(logo_path, (width - logo_width) / 2, y, logo_width, logo_height)
        y -= logo_height + 10
    else:
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(width / 2, y, "P")
        y -= 40

    # Titre du reçu
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(width / 2, y, "***** Reçu de Commande *****")
    y -= 15

    # Détails de la commande
    pdf.setFont("Helvetica", 8)
    pdf.drawString(10, y, f"Numéro: {commande.numero_commande}")
    pdf.drawString(120, y, f"Date: {commande.date_creation.strftime('%b. %d, %Y')}")
    y -= 15

    # Ligne de séparation
    pdf.line(10, y, width - 10, y)
    y -= 15

    # En-tête du tableau
    pdf.drawString(10, y, "Pièce")
    pdf.drawString(50, y, "Qte")
    pdf.drawString(100, y, "P.U")
    pdf.drawString(150, y, "Total")
    y -= 10
    pdf.line(10, y, width - 10, y)
    y -= 15

    # Détails des articles
    for item in panier_items:
        pdf.drawString(10,  y, f"{item.piece.designation}")
        pdf.drawString(50,  y, f"{item.quantite}")
        pdf.drawString(100, y, f"{item.piece.prix_unitaire}")
        pdf.drawString(150, y, f"{item.quantite * item.piece.prix_unitaire}")
        y -= 15
    y -= 10

    pdf.line(10, y, width - 10, y)
    y -= 15

    # Totaux
     # Totaux alignés avec une distance de 100
    pdf.drawString(10, y, "Total:")
    pdf.drawString(135, y, f"{commande.total} Fcfa")
    y -= 15
    pdf.drawString(10, y, "Remise:")
    pdf.drawString(135, y, "0.00 %")
    y -= 15
    pdf.drawString(10, y, "Payé:")
    pdf.drawString(135, y, f"{commande.montant_paye} Fcfa")
    y -= 15
    pdf.drawString(10, y, "Rendu:")
    pdf.drawString(135, y, f"{commande.montant_reste} Fcfa")
    y -= 15

    # QR Code
    qr = qrcode.make(f"Commande: {commande.numero_commande}")
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_image = Image.open(qr_buffer)
    pdf.drawInlineImage(qr_image, width / 2 - 25, y - 50, 50, 50)
    y -= 65

    # Message de remerciement
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(width / 2, y, "Merci pour votre achat !")
    y -= 10
    pdf.drawCentredString(width / 2, y, "Contact : PBGentreprise@admin.com")
    y -= 10
    pdf.drawCentredString(width / 2, y, "*** A tes résolutions repondra le succès ***")
    y -= 10

    pdf.save()
    buffer.seek(0)
    return buffer

@user_passes_test(is_caissier, is_admin_magasin)
def valider_paiement(request, ticket_id):
    paiement_non_valide = Panier.objects.filter(valide=True, panier_paye=False)
    ticket = get_object_or_404(Ticket, numero=ticket_id, utilise=False)
    commande = ticket.commande
    panier = commande.panier

    if request.method == 'POST':
        montant = request.POST.get('montant')
        if float(montant) >= commande.total:
            commande.paye = True
            reste = float(montant) - float(commande.total)
            commande.utilisateur = request.user
            commande.montant_paye = float(montant)
            commande.montant_reste = abs(reste)
            commande.paye
            commande.save()
        
            ticket.utilise = True
            ticket.utilisateur = request.user
            ticket.save()

            panier.panier_paye = True
            panier.save()

            for item in PanierItem.objects.filter(panier=panier):
                piece = item.piece
                piece.quantite -= item.quantite
                piece.save()
            messages.success(request, f"Paiement effectué.")
            # Génération du reçu PDF
            panier_items = PanierItem.objects.filter(panier=panier)
            pdf_buffer = generate_receipt_pdf(commande, panier_items, ticket)
            
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="recu_{commande.numero_commande}.pdf"'
            return response

        else:
            messages.error(request, f"Le montant payé ne correspond pas au total de la commande.")
            return redirect('piece_list_accueil')
            
    panier_items = PanierItem.objects.filter(panier=panier)
    context = {
        'ticket': ticket,
        'commande': commande,
        'paiement_non_valide': paiement_non_valide,
        'panier_items': panier_items,
    }
    return render(request, 'caissiere_validation_paiement.html', context)


# from django.http import JsonResponse
# @user_passes_test(is_caissier, is_admin_magasin)
# def valider_paiement(request, ticket_id):
#     paniers_non_valides = Panier.objects.filter(valide=True, panier_paye=False)
#     ticket = get_object_or_404(Ticket, numero=ticket_id, utilise=False)
#     commande = ticket.commande
#     panier = commande.panier
#     if request.method == 'POST':
#         montant = request.POST.get('montant')
#         if float(montant) >= commande.total:
#             commande.paye = True
#             reste = float(montant) - float(commande.total)
#             commande.utilisateur = request.user
#             commande.montant_paye = float(montant)
#             commande.montant_reste = abs(reste)
#             commande.paye
#             commande.save()
#             ticket.utilise = True
#             ticket.utilisateur = request.user
#             ticket.save()
#             panier.panier_paye = True
#             panier.save()
           
#             # Mettre à jour le stock
#             for item in PanierItem.objects.filter(panier=panier):
#                 piece = item.piece
#                 piece.quantite -= item.quantite
#                 piece.save()

#             # Générer les données du reçu
#             panier_items = PanierItem.objects.filter(panier=panier)
#             receipt_data = {
#                 'commande_numero': commande.numero_commande,
#                 'total': commande.total,
#                 'montant_paye': commande.montant_paye,
#                 'montant_reste': commande.montant_reste,
#                 'panier_items': [
#                     {
#                         'designation': item.piece.designation,
#                         'quantite': item.quantite,
#                         'prix_unitaire': item.piece.prix_unitaire
#                     }
#                     for item in panier_items
#                 ]
#             }
#             # Renvoie les données du reçu en réponse AJAX
#             return JsonResponse({
#                 'success': True,
#                 'receipt_data': receipt_data,
#                 'message': f"Paiement validé. Utilisez le numéro {ticket.numero} pour récupérer vos articles."
#             })
#         else:
#             return JsonResponse({
#                 'success': False,
#                 'message': "Le montant payé ne correspond pas au total de la commande."
#             })

#     panier_items = PanierItem.objects.filter(panier=panier)
#     context = {
#         'ticket': ticket,
#         'commande': commande,
#         'paniers_non_valides': paniers_non_valides,
#         'panier_items': panier_items,
#     }
#     return render(request, 'caissiere_validation_paiement.html', context)
@user_passes_test(is_liveur)
def livraison_accueil(request):
    ticket = get_object_or_404(Ticket,  utilise=True)
    return render(request, 'valider_livraison.html',  {'ticket': ticket})

def valider_livraison(request, ticket_id):
    try:
        ticket = get_object_or_404(Ticket, numero=ticket_id, utilise=True)
        panier_non_livre = Panier.objects.filter(ticket=ticket.numero).first()
        panier_non_livre.panier_livre = True
        panier_non_livre.save()
        messages.success(request, f"Livraison validée pour le ticket {ticket.numero}.")
    except Exception as e:
        messages.error(request, f"Erreur lors de la validation de la livraison : {str(e)}")
    return redirect(request.META.get('HTTP_REFERER', 'livraison_dashboard'))

@user_passes_test(is_accueillant)
def accueil(request):
    return render(request, 'accueil.html')

@user_passes_test(is_caissier)
def caisseDashboard(request):
    paniers_non_valides = Panier.objects.filter(valide=True,panier_paye = False,panier_livre=False)
    user = request.user
    role = None
    if hasattr(user, 'profile'):
        role = user.profile.role
    form = DateForm(request.GET)
    if form.is_valid():
        date_debut = form.cleaned_data['date_debut']
        date_fin = form.cleaned_data['date_fin']

        total_revenue_jour = Commande.objects.filter(utilisateur=user, date_creation__range=[date_debut, date_fin]).aggregate(total=Sum('total'))['total'] or 0
        if role in ['AdminMagasin', 'superadmin']:
            paniers = Panier.objects.filter(valide=True,date_creation__range=[date_debut, date_fin])
        else:
            # Show only paniers related to the connected user
            paniers = Panier.objects.filter(utilisateur=user, valide=True, date_creation__range=[date_debut, date_fin])
        
        total_pieces = Piece.objects.aggregate(total=Sum('quantite'))['total'] or 0
        total_inventory_value = Piece.objects.aggregate(total_value=Sum(ExpressionWrapper(F('prix_unitaire') * F('quantite'), output_field=DecimalField())))['total_value'] or 0

        panier_valide = PanierItem.objects.filter(panier__in=paniers, date_creation__range=[date_debut, date_fin]).count()
        command_valide = Commande.objects.filter(panier__in=paniers, date_creation__range=[date_debut, date_fin]).count()
        
        command_valide_en_attente = Commande.objects.filter(utilisateur=user, paye=False, panier__in=paniers, date_creation__range=[date_debut, date_fin]).count()
        total_revenue_jour_paye = Commande.objects.filter(utilisateur=user, paye=True, date_creation__range=[date_debut, date_fin]).aggregate(total=Sum('total'))['total'] or 0
        total_revenue_mois_an_paye = Commande.objects.filter(utilisateur=user, paye=True, date_creation__range=[date_debut, date_fin]).aggregate(total=Sum('total'))['total'] or 0
        total_revenue_an_paye = Commande.objects.filter(utilisateur=user, paye=True, date_creation__range=[date_debut, date_fin]).aggregate(total=Sum('total'))['total'] or 0
        
        print(total_revenue_jour,"-------------------------",panier_valide,"-------------------------",command_valide)

        pieces = Piece.objects.filter(quantite__gt=0)
        # Retrieve or create the cart for the current user
        panier, created = Panier.objects.get_or_create(utilisateur=request.user, valide=False)
        
        panier_items = PanierItem.objects.filter(panier=panier)
        for item in panier_items:
            item.total = item.piece.prix_unitaire * item.quantite
        sous_total = sum(item.total for item in panier_items)
        total_revenue_mois = Commande.objects.filter(utilisateur=user, date_creation__year=date.today().year, date_creation__month=date.today().month).aggregate(total=Sum('total'))['total'] or 0
        nb_command_valide_mois = Commande.objects.filter(utilisateur=user, date_creation__year=date.today().year, date_creation__month=date.today().month).count()
        nb_panier_mensuelle_valide = PanierItem.objects.filter(panier__utilisateur=user, date_creation__year=date.today().year, date_creation__month=date.today().month).count()
        
    else:
        
        # Check if the user is a superadmin or adminMagasin
        if role in ['AdminMagasin', 'superadmin']:
            # Show all panier instances
            paniers = Panier.objects.filter(valide=True, date_creation=date.today())
        else:
            # Show only paniers related to the connected user
            paniers = Panier.objects.filter(utilisateur=user, valide=True, date_creation=date.today())
        
        total_pieces = Piece.objects.aggregate(total=Sum('quantite'))['total'] or 0
        panier_valide = PanierItem.objects.filter(panier__in=paniers).count()
        nb_panier_mensuelle_valide = PanierItem.objects.filter(panier__utilisateur=user, date_creation__year=date.today().year, date_creation__month=date.today().month).count()
        total_inventory_value = Piece.objects.aggregate(total_value=Sum(ExpressionWrapper(F('prix_unitaire') * F('quantite'), output_field=DecimalField())))['total_value'] or 0
        
        command_valide_en_attente = Commande.objects.filter(utilisateur=user, paye=False, panier__in=paniers, date_creation=date.today()).count()
        total_revenue_jour_paye = Commande.objects.filter(utilisateur=user, paye=True, date_creation=date.today()).aggregate(total=Sum('total'))['total'] or 0
        total_revenue_mois_an_paye = Commande.objects.filter(utilisateur=user, paye=True, date_creation__year=date.today().year, date_creation__month=date.today().month).aggregate(total=Sum('total'))['total'] or 0
        total_revenue_an_paye = Commande.objects.filter(utilisateur=user, paye=True, date_creation__year=date.today().year).aggregate(total=Sum('total'))['total'] or 0

        panier_items = PanierItem.objects.filter(panier__in=paniers)
        pieces = Piece.objects.filter(quantite__gt=0)
        # Retrieve or create the cart for the current user
        panier, created = Panier.objects.get_or_create(utilisateur=request.user, valide=False)
        panier_items = PanierItem.objects.filter(panier=panier)
        # Calculate totals
        for item in panier_items:
            item.total = item.piece.prix_unitaire * item.quantite
        sous_total = sum(item.total for item in panier_items)
    context = {
        'total_pieces': total_pieces,
        'total_inventory_value': total_inventory_value,
        'pieces': pieces,
        'panier_items': panier_items,
        'sous_total': sous_total,
        'form': form,
        'panier_valide': panier_valide or 0,
        
        'command_valide_en_attente' : command_valide_en_attente,
        'total_revenue_jour_paye': total_revenue_jour_paye,
        'total_revenue_mois_an_paye' : total_revenue_mois_an_paye,
        'total_revenue_an_paye' : total_revenue_an_paye
    }
    return render(request, 'caissiere_validation_paiement.html', context)

@user_passes_test(is_liveur)
def livraison_dashboard(request):
    # Filtrer les paniers dont le statut 'valide' est True
    livraison_en_attente = Panier.objects.filter(valide=True, panier_paye=True, panier_livre=False) 
    nb_en_attente = Panier.objects.filter(valide=True, panier_paye=True, panier_livre=False, date_creation=date.today()).count() 
    livraison_effectuee = Panier.objects.filter(valide=True, panier_paye=True, panier_livre=True) 
    # livraison_effectuee = Panier.objects.filter(valide=True, panier_paye=True, panier_livre=True, date_creation=date.today()) 
    nb_effectuee = Panier.objects.filter(valide=True, panier_paye=True, panier_livre=True,).count() 
    return render(request, 'livraison.html', {
        'livraison_en_attente': livraison_en_attente,
        'livraison_effectuee': livraison_effectuee,
        'nb_en_attente': nb_en_attente,
        'nb_effectuee': nb_effectuee,
        })


# import qrcode
# import io
# import base64
# from django.shortcuts import render, get_object_or_404
# from .models import Commande, PanierItem

# def generate_receipt(request, commande_id):
#     # Récupérer la commande basée sur l'ID
#     commande = get_object_or_404(Commande, id=commande_id)

#     # Calculer le montant restant (s'il n'est pas déjà calculé)
#     if commande.total and commande.montant_paye:
#         commande.montant_reste = commande.montant_paye - commande.total 

#     # Récupérer les pièces dans le panier de la commande
#     panier = commande.panier
#     panier_items = PanierItem.objects.filter(panier=panier)

#     # Générer un QR code avec une taille réduite
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=5,  # Réduit la taille des pixels du QR code
#         border=2,    # Réduit la largeur de la bordure
#     )
#     qr_data = f"Commande #{commande.numero_commande} - Total: {commande.total} Fcfa - Date : {commande.date_creation}"
#     qr.add_data(qr_data)
#     qr.make(fit=True)

#     # Convertir le QR code en image et l'encoder en base64
#     img = qr.make_image(fill='black', back_color='white')
#     buffer = io.BytesIO()
#     img.save(buffer, format="PNG")
#     img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

#     # Rendre la page du reçu avec QR code et détails des pièces
#     return render(request, 'reçu.html', {
#         'commande': commande,
#         'qr_code_img': img_str,
#         'panier_items': panier_items
#     })

#scanne 
from django.shortcuts import render, get_object_or_404
from .models import Commande

def details_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    return render(request, 'details_commande.html', {'commande': commande})

def scanner_qr_code(request):
    return render(request, 'scanner.html')


#historique 

from django.shortcuts import render
from django.utils.dateparse import parse_date
from datetime import datetime
from .models import Panier, PanierItem, Piece, Commande, Ticket

@user_passes_test(is_admin_magasin)
def global_history_view(request):
    filter_date = request.GET.get('date', None)
    
    # Si aucune date n'est fournie, on utilise la date du jour
    if filter_date:
        filter_date_obj = parse_date(filter_date)
    else:
        filter_date_obj = datetime.today().date()

    # Obtenez l'utilisateur connecté
    current_user = request.user

    # Récupérer l'historique des objets pour différents modèles
    history_diff = []
    models = [Panier, PanierItem, Piece, Commande, Ticket]

    for model in models:
        model_history = model.history.filter(history_date__date=filter_date_obj)
        for record in model_history:
            if record.prev_record:
                diff = record.diff_against(record.prev_record)
                history_diff.append({
                    'record': record,
                    'model': model.__name__,
                    'changed_fields': diff.changed_fields
                })
            else:
                history_diff.append({
                    'record': record,
                    'model': model.__name__,
                    'changed_fields': None
                })

    context = {
        'global_history': history_diff,
        'filter_date': filter_date_obj,
        'current_user': current_user
    }

    return render(request, 'global_history.html', context)
