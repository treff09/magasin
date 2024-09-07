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
    
        # AFFICHAGE DES DONNEES DU JOUR EN COURS
        
        total_pieces = Piece.objects.aggregate(total=Sum('quantite'))['total'] or 0
        # Total inventaire
        total_inventory_value = Piece.objects.aggregate(total_value=Sum(ExpressionWrapper(F('prix_unitaire') * F('quantite'), output_field=DecimalField())))['total_value'] or 0
        # Total Commandes
        total_orders = Commande.objects.filter(date_creation=date.today()).count()
        # Total revenue Commandes
        # total_revenue = Commande.objects.aggregate(total=Sum('total'))['total'] or 0
        total_revenue_jour = Commande.objects.filter(date_creation=date.today()).aggregate(total=Sum('total'))['total'] or 0
        total_revenue_mois = Commande.objects.filter(date_creation__year=date.today().year, date_creation__month=date.today().month).aggregate(total=Sum('total'))['total'] or 0
        
        print('')
        print('----------------------------------------------------------------', total_revenue_jour,'------------------------',total_revenue_mois,'-----------------',total_inventory_value)
        print('')
        # Total impayés
        total_unpaid = Commande.objects.aggregate(total=Sum('montant_reste'))['total'] or 0
        total_unpaid_jour = Commande.objects.filter(date_creation=date.today()).aggregate(total=Sum('montant_reste'))['total'] or 0
        total_unpaid_mois = Commande.objects.filter(date_creation__year=date.today().year, date_creation__month=date.today().month).aggregate(total=Sum('montant_reste'))['total'] or 0
        
        # Nombre de tickets émis et utilisés
        total_tickets_issued = Ticket.objects.filter(date_creation=date.today()).count()

        total_tickets_used = Ticket.objects.filter(utilise=True, date_creation=date.today()).count()
        # Commandes entièrement payées et livrées
        fully_paid_delivered_orders = Commande.objects.filter(paye=True, panier__panier_livre=True,date_creation=date.today(),).count()
        # Commandes en attente de paiement
        pending_payment_orders = Commande.objects.filter(paye=False, date_creation=date.today()).count()

        # Pièces dont le stock est faible
        low_stock_pieces = Piece.objects.filter(quantite__lte=5).count()
        # Total Paniers
        total_paniers = Panier.objects.all().count()
        total_paniers_jour = Panier.objects.filter(date_creation=date.today()).count()
        #le mois en cours
        total_paniers_mois = Panier.objects.filter(date_creation__year=date.today().year, date_creation__month=date.today().month).count()
        # Estimation du stock
        estimat_stock = (total_pieces/total_paniers)
        if total_paniers == 0:
            estimat_stock = 0
        estimat_stock_format = '{:.2f}'.format(estimat_stock)
        # Paniers that are validated but not yet paid
        validated_paniers = Panier.objects.filter(valide=True, panier_paye=False, date_creation=date.today()).count()
        #----------------------------------------------------------------------------#
        pieces_by_category_alto = Piece.objects.filter(type_voiture__type_voiture__in=['ALTO']).count()
        pieces_by_category_dzire = Piece.objects.filter(type_voiture__type_voiture__in=['DZIRE']).count()
        pieces_by_category_swift = Piece.objects.filter(type_voiture__type_voiture__in=['SWIFT']).count()
        total_inventory_restant = total_inventory_value - total_revenue_mois

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
            panier__commands__isnull=False,date_creation=date.today()
        ).aggregate(total_pieces=Sum('quantite'))['total_pieces'] or 0

        #--------------------------------------Graphs--------------------------------#

        total_revenue_filtre = Commande.objects.filter(date_creation__year=datetime.now().year)
        revenue_mensuelle_filtre = {month: 0 for month in range(1, 13)}
        for commande in total_revenue_filtre:
            revenue_mensuelle_filtre[commande.date_creation.month] += 1

        revenue_mensuelle_data = [revenue_mensuelle_filtre[month] for month in range(1, 13)]
        mois_label = [calendar.month_name[month][:2] for month in range(1, 13)]

        # Ajouter ces données au contexte

        # print("--------------------------------")
        # print(total_revenue_filtre,"--------------------------------",revenue_mensuelle_data,date.today() + timedelta(days=1))
        # print("--------------------------------")

        # print(total_pieces_swift,"-----------",total_pieces_alto,"-----------",total_pieces_dzire,"-----------",total_quantite_alto)

        form = self.form_class(self.request.GET)
        if form.is_valid():
            date_debut = form.cleaned_data['date_debut'] 
            date_fin = form.cleaned_data['date_fin'] 
            print('date_debut', 'Date de debut invalide', 'danger')
        
        #La categorie ayant vendu le pluse de piece 1er au 3ieme
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
                )
            )
            .order_by('-total_pieces')[:3] 
        )

        #Les pièces les plus vendues
        top_pieces = (
            PanierItem.objects.filter(date_creation=date.today(),
                                      panier__valide=True,         
                                      panier__panier_paye=True,)
            .values('piece__designation', 'piece__type_voiture__type_voiture')  
            .annotate(total_commandes=Count('id'), total_somme=Sum('piece__prix_unitaire'))  
            .order_by('-total_commandes')[:2]  
        )
        # best_pieces = sorted([x for x in best_pieces if x['recs'] is not None], key=lambda x: x['recs'], reverse=True)[:10]
        print(top_pieces,"--------++++++++++++++++-------",top_categories)
        
        
        context = {
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
        'mois_label': mois_label,
        'total_pieces': total_pieces,
        'total_inventory_value': total_inventory_value,
        'total_orders': total_orders,
        'total_revenue_jour': total_revenue_jour,
        'total_unpaid': total_unpaid,
        'total_unpaid_jour': total_unpaid_jour,
        'total_unpaid_mois': total_unpaid_mois,
        'total_tickets_issued': total_tickets_issued,
        'total_tickets_used': total_tickets_used,
        'fully_paid_delivered_orders': fully_paid_delivered_orders,
        'pending_payment_orders': pending_payment_orders,
        'low_stock_pieces': low_stock_pieces,
        'total_paniers': total_paniers,
        'total_paniers_jour': total_paniers_jour,
        'total_revenue_mois': total_revenue_mois,
        'total_inventory_value': total_inventory_value,
        'total_paniers_mois': total_paniers_mois,
        'total_inventory_restant': total_inventory_restant,
        'validated_paniers': validated_paniers,
        'pieces_by_category_alto': pieces_by_category_alto,
        'pieces_by_category_swift': pieces_by_category_swift,
        'pieces_by_category_dzire': pieces_by_category_dzire,
        'estimat_stock_format': estimat_stock_format,
        }
        return context
        
        
#         Total_recettes = sum(recet.montant for recet in recette)
#         Total_recette_format ='{:,}'.format(Total_recettes).replace('',' ')
        # recette_mois = Recette.objects.annotate(mois_de_recettes=ExtractMonth("date")).values("mois_de_recettes").annotate(total_recet=Sum("montant")).values("mois_de_recettes","total_recet").order_by('mois_de_recettes')
        # charg_var_mois = ChargeVariable.objects.annotate(month_chvar=ExtractMonth("date")).values("month_chvar").annotate(total_chvar=Sum("montant")).values("month_chvar","total_chvar").order_by('month_chvar')
        # month_piece =[]
        # marg_par_mois = []
        # for reccete, chargess in zip(recette_mois,charg_var_mois):
        #     month_recets = (calendar.month_name[reccete['mois_de_recettes']][:2])
        #     if month_recets:
        #         month_recets = (calendar.month_name[reccete['mois_de_recettes']][:2])
        #     else:
        #         month_recets = (calendar.month_name[reccete['mois_de_recettes']][:2])
        #     cumul_recettes = reccete['total_recet']
        #     cumul_charges = chargess['total_chvar'] if chargess['total_chvar'] else 0
        #     marge = cumul_recettes - cumul_charges
        #     if cumul_recettes==0:
        #         taux =0
        #     else:
        #         taux = round(((marge)*100/cumul_recettes),2)
        # if marg_par_mois:
        #     marg_par_mois.append({'month_recets': month_recets, 'marge': marge,'taux':taux})
        # else:
        #     marg_par_mois.append({})
        
# #-----------------------------------Pour Faire les filtre selon les dates entrées---------------------------------
#         form = self.form_class(self.request.GET)
#         if form.is_valid():
#             date_debut = form.cleaned_data['date_debut'] 
#             date_fin = form.cleaned_data['date_fin'] 
            
#             recettes = Recette.objects.filter(date__range=[date_debut, date_fin]).aggregate(Sum('montant'))['montant__sum'] 
#             context['recettes_totales'] = recettes if recettes is not None else 0
            
#             piecs = Piece.objects.filter(date_achat__range=[date_debut, date_fin]).aggregate(Sum('cout'))['cout__sum'] 
#             context['pieces_totales'] = piecs if piecs is not None else 0
            
#             charges_variables = ChargeVariable.objects.filter(date__range=[date_debut, date_fin]).aggregate(Sum('montant'))['montant__sum']
#             context['charges_variables_totales'] = charges_variables if charges_variables is not None else 0
            
#             charges_fixe = ChargeFixe.objects.filter(date__range=[date_debut, date_fin]).aggregate(Sum('montant'))['montant__sum']
#             context['charges_fixes_totales'] = charges_fixe if charges_fixe is not None else 0
            
#             context['charges_totales'] =charges_fixe + context['charges_variables_totales'] if charges_fixe is not None else 0

#             context['marge_totale'] = recettes - context['charges_variables_totales'] if recettes is not None else 0

#             taux_recette = Recette.objects.filter(date__range=[date_debut, date_fin]).aggregate(Sum('montant'))['montant__sum'] or 1
#             taux_diviseur = context['recettes_totales'] - (context['charges_variables_totales'])
            
#             context['taux_vehi'] = round(taux_diviseur*100/ taux_recette, 2 ) if taux_recette is not None and taux_diviseur is not None else 0
            
#             taux_mois= round(taux_diviseur*100/ taux_recette, 2 ) if taux_recette is not None and taux_diviseur is not None else 0
#             context['taux_par_mois'] = [taux_mois] * 12 if taux_recette else [0] * 12

#             resultat = (context['recettes_totales'] - context['charges_totales'])
#             context['resultat_total'] = resultat if resultat is not None else 0
            
# #-------------------------------------------Pour les Graphes---------------------------------------------
#             recets = Recette.objects.filter(date__range=[date_debut, date_fin])
#             charvars = ChargeVariable.objects.filter(date__range=[date_debut, date_fin])
#             charfix = ChargeFixe.objects.filter(date__range=[date_debut, date_fin])
#             pieces = Piece.objects.filter(date_achat__range=[date_debut, date_fin])
            
#             recettes_mensuelles = {month: 0 for month in range(1, 13)}
#             charges_variables_mensuelles = {month: 0 for month in range(1, 13)}
#             charges_fixe_mensuelles = {month: 0 for month in range(1, 13)}
#             piece_mensuelles = {month: 0 for month in range(1, 13)}
            
#             for recette in recets:
#                 recettes_mensuelles[recette.date.month] += recette.montant
                
#             for charge_variable in charvars:
#                 charges_variables_mensuelles[charge_variable.date.month] += charge_variable.montant
            
#             for charge_fixe in charfix:
#                 charges_fixe_mensuelles[charge_fixe.date.month] += charge_fixe.montant
            
#             for piec in pieces:
#                 piece_mensuelles[piec.date_achat.month] += piec.cout
            
#             piece_data = [piece_mensuelles[month] for month in range(1, 13)]
#             piece_data = [0 if piec == 0 else piece_data[i - 1] for i, piec in enumerate(piece_data, start=1)]
            
#             recette_data = [recettes_mensuelles[month] for month in range(1, 13)]
#             recette_data = [0 if recette == 0 else recette_data[i - 1] for i, recette in enumerate(recette_data, start=1)]
            
#             charg_vari_data = [charges_variables_mensuelles[month] for month in range(1, 13)]
#             charg_vari_data = [0 if charge_variable == 0 else charg_vari_data[i - 1] for i, charge_variable in enumerate(charg_vari_data, start=1)]
            
#             charg_fixe_data = [charges_fixe_mensuelles[month] for month in range(1, 13)]
#             charg_fixe_data = [0 if charge_fixe == 0 else charg_fixe_data[i - 1] for i, charge_fixe in enumerate(charg_fixe_data, start=1)]
            
#             marges_mensuelles = {month: recettes_mensuelles[month] - charges_variables_mensuelles[month] for month in range(1, 13)}
#             taux_mensuels = {month: (marges_mensuelles[month] * 100) / recettes_mensuelles[month] if recettes_mensuelles[month] > 0 else 0 for month in range(1, 13)}
#             context['labels'] = [month[:2] for month in list(calendar.month_name)[1:]]
            
#             taux_data = [taux_mensuels[month] for month in range(1, 13)]
#             taux_data = [0 if taux == 0 else taux_data[i - 1] for i, taux in enumerate(taux_data, start=1)]
            
#             marge_contri = []
#             all_vehicule = Vehicule.objects.all()[:6]
#             all_recettes= Recette.objects.all()[:5]
#             best_recets = []
#             best_marge = []
#             best_taux = []
#             for vehicule in all_vehicule:
#                 recs = Recette.objects.filter(vehicule=vehicule, date__range=[date_debut, date_fin]).aggregate(Sum('montant'))['montant__sum'] 
#                 context['rece_all'] = recs if recs is not None else 0
                
#                 charges_variables = ChargeVariable.objects.filter(vehicule = vehicule, date__range=[date_debut, date_fin]).aggregate(Sum('montant'))['montant__sum']
#                 context['chargvari_all'] = charges_variables if charges_variables is not None else 0
                
#                 marge_cont = context['rece_all'] - context['chargvari_all']
#                 context['marge'] = marge_cont if marge_cont is not None else 0
                
#                 if context['rece_all'] == 0:
#                     context['taux'] =0
#                 else:
#                     taux = round((context['marge']*100)/context['rece_all'],2)
#                     context['taux'] = taux if taux is not None else 0
                    
#                 best_taux.append({'vehicule': vehicule, 'taux':context['taux']})
#                 best_marge.append({'vehicule': vehicule, 'marge_cont':marge_cont})
#                 best_recets.append({'vehicule': vehicule, 'recs':recs})
#             best_marge = sorted([x for x in best_marge if x['marge_cont'] is not None], key=lambda x: x['marge_cont'], reverse=True)[:5] 
#             best_taux = sorted(best_taux, key=lambda x: x['taux'], reverse=True)[:5]
#             best_recets = sorted([x for x in best_recets if x['recs'] is not None], key=lambda x: x['recs'], reverse=True)[:5] 
            
#             context['taux_data'] = taux_data
#             context['best_taux'] = best_taux
#             context['best_marge'] = best_marge
#             context['best_recets'] = best_recets
#             context['recette_data'] = recette_data
#             context['charg_vari_data'] = charg_vari_data
#             context['charg_fixe_data'] = charg_fixe_data
#             context['piece_data'] = piece_data
#         else:
#             all_vehicule = Vehicule.objects.all()[:5]
#             marge_contri = []
#             best_taux = []
#             recettes= Recette.objects.all()[:5]
#             top_recets = []
#             for vehicule in all_vehicule:
#                 total_recets = Recette.objects.filter(vehicule = vehicule).aggregate(Sum('montant'))['montant__sum'] or 1
#                 total_charg_var = ChargeVariable.objects.filter(vehicule = vehicule).aggregate(Sum('montant'))['montant__sum'] or 0
#                 marge_contribution = total_recets - total_charg_var
#                 taux = round(((marge_contribution)*100/total_recets),2)
#                 marge_contri.append({'vehicule': vehicule, 'marge_contribution':marge_contribution})
#                 best_taux.append({'vehicule': vehicule,'taux':taux})
#                 top_recets.append({'vehicule': vehicule, 'total_recets':total_recets})
# #-------    ----------------------Top marge----------------------------
#             marge_contri = sorted(marge_contri, key=lambda x: x['marge_contribution'], reverse=True)[:5]    
#             best_taux = sorted(best_taux, key=lambda x: x['taux'], reverse=True)[:5]    
#             top_recets = sorted(top_recets, key=lambda x: x['total_recets'], reverse=True)[:5]
            
#             context['marge_contri'] = marge_contri
#             context['best_taux'] = best_taux
#             context['top_recets'] = top_recets
#             context['labels'] = [month[:2] for month in list(calendar.month_name)[1:]]
#             context['taux_data'] = [0] * 12
#         context['form'] = form
        
#         catego_vehi = CategoVehi.objects.all()
#         context['categories'] = CategoVehi.objects.all()
#         categorie_id = self.request.GET.get('categorie')
#         if categorie_id:
#             categorie = CategoVehi.objects.get(pk=categorie_id)
#             context['somme_par_categorie'] = Recette.objects.filter(vehicule_id__category=categorie).aggregate(Sum('montant'))['montant__sum']
#         else:
#             context['somme_par_categorie'] = Recette.objects.all().aggregate(Sum('montant'))['montant__sum']
        
# #_____________________________TOTAL DES CHARGES VARIABLES_____________________________#
#         cahargevariable = ChargeVariable.objects.all()
#         Total_charg_var = sum(chargvar.montant for chargvar in cahargevariable)
        
#         Total_charg_var_format ='{:,}'.format(Total_charg_var).replace('',' ')
# #_____________________________TOTAL DES CHARGES FIXES_____________________________#       
#         chargefix = ChargeFixe.objects.all()
#         Total_charg_fix = sum(chargfix.montant for chargfix in chargefix)
#         Total_charg_fix_format ='{:,}'.format(Total_charg_fix).replace('',' ')
# #_____________________________TOTAL DES CHARGES_____________________________#
#         total_charg = Total_charg_fix + Total_charg_var
#         total_charge_format ='{:,}'.format(total_charg).replace('',' ')
# #_____________________________MARGE CONTRIBUTION_____________________________#
#         marge_contribution = Total_recettes - Total_charg_var
# #_____________________________TAUX CONTRIBUTION_____________________________#
#         if Total_recettes == 0:
#             taux_marge = 0
#         else:
#             taux_marge = (marge_contribution*100/(Total_recettes))
#         taux_marge_format ='{:.2f}'.format(taux_marge)
# #_____________________________RESULTAT_____________________________#
#         resultat = Total_recettes - total_charg
#         resultat_format ='{:,}'.format(resultat).replace('',' ')
# #_________________________________PIECE______________________________#
#         piece = Piece.objects.all()
#         totl_piece = sum(piece.cout for piece in piece)
#         totl_piece_format ='{:,}'.format(totl_piece).replace('',' ')
        
#         total_piece_mois = Piece.objects.annotate(month_piece=ExtractMonth("date_achat")).values("month_piece").annotate(total_piece=Sum("cout")).values("month_piece","total_piece")
#         month_piece =[]
#         total_piece = []
#         for i in total_piece_mois:
#             month_piece.append(calendar.month_name[i["month_piece"]][:2])
#             total_piece.append(i['total_piece'])
        
#         #-------------------------------------------Pour les Graphes---------------------------------------------
#         recets = Recette.objects.all()
#         charvars = ChargeVariable.objects.all()
#         charfix = ChargeFixe.objects.all()
#         piecs = Piece.objects.all()
        
#         recettes_mensuelles = {month: 0 for month in range(1, 13)}
#         charges_variables_mensuelles = {month: 0 for month in range(1, 13)}
#         charges_fixe_mensuelles = {month: 0 for month in range(1, 13)}
#         piece_mensuelles = {month: 0 for month in range(1, 13)}
        
#         for recette in recets:
#             recettes_mensuelles[recette.date.month] += recette.montant
            
#         for charge_variable in charvars:
#             charges_variables_mensuelles[charge_variable.date.month] += charge_variable.montant
        
#         for charge_fixe in charfix:
#             charges_fixe_mensuelles[charge_fixe.date.month] += charge_fixe.montant
        
#         for piec in piecs:
#             piece_mensuelles[piec.date_achat.month] += piec.cout
            
#         recette_mois_data = [recettes_mensuelles[month] for month in range(1, 13)]
#         recette_mois_data = [0 if recette == 0 else recette_mois_data[i - 1] for i, recette in enumerate(recette_mois_data, start=1)]
#         context['recette_mois_data'] = recette_mois_data
#         context['label_recette_mois'] = [month[:2] for month in list(calendar.month_name)[1:]]
        
#         charg_fixe_mois_data = [charges_fixe_mensuelles[month] for month in range(1, 13)]
#         charg_fixe_mois_data = [0 if charge_fixe == 0 else charg_fixe_mois_data[i - 1] for i, charge_fixe in enumerate(charg_fixe_mois_data, start=1)]
#         context['charg_fixe_mois_data'] = charg_fixe_mois_data
        
#         charg_vari_mois_data = [charges_variables_mensuelles[month] for month in range(1, 13)]
#         charg_vari_mois_data = [0 if charge_variable == 0 else charg_vari_mois_data[i - 1] for i, charge_variable in enumerate(charg_vari_mois_data, start=1)]
#         context['charg_vari_mois_data'] = charg_vari_mois_data
        
#         piece_mois_data = [piece_mensuelles[month] for month in range(1, 13)]
#         context['piece_mois_data'] = [0 if piec == 0 else piece_mois_data[i - 1] for i, piec in enumerate(piece_mois_data, start=1)]
           
#         mois = list(range(1, 13))
#         total_recettes_mois = [0] * 12
#         total_charges_variables_mois = [0] * 12
        
#         for re in recette_mois:
#             total_recettes_mois[re['mois_de_recettes'] - 1] = re['total_recet']
#         for chvar in charg_var_mois:
#             total_charges_variables_mois[chvar['month_chvar'] - 1] = chvar['total_chvar']
#         context['taux_mois'] = [round(((total_recet - chvar) * 100) / total_recet, 2) if total_recet > 0 else 0 for total_recet, chvar in zip(total_recettes_mois, total_charges_variables_mois)]
    
#         mois_noms = [calendar.month_name[mois][:2] for mois in mois]
#         context['mois_noms'] = mois_noms
        
#         context['label_mois'] = [month[:2] for month in list(calendar.month_name)[1:]]
#         #somme_recettes_par_categorie_aujourd = []
#         #for categorie in categories:
#         #    vehicules_categorie = Vehicule.objects.filter(category=categorie)
#         #    recettes_categorie = Recette.objects.filter(vehicule__in=vehicules_categorie, date=date.today())
#         #    somme_recette = recettes_categorie.aggregate(Sum('montant'))['montant__sum'] or 0
#         #    somme_recettes_par_categorie_aujourd.append({
#         #        'categorie': categorie.category,
#         #        'somme_recette': somme_recette
#         #    })
#         #print("------------Aujourd'hui--------------", somme_recettes_par_categorie_aujourd)
#         context['catego_vehi'] = catego_vehi
#         context['marge_contri'] = marge_contri
#         context['total_piece'] = total_piece
#         context['month_piece'] = month_piece
#         context['Total_recette_format'] = Total_recette_format
#         context['Total_charg_fix_format'] = Total_charg_fix_format
#         context['Total_charg_var_format'] = Total_charg_var_format
#         context['total_charge_format'] = total_charge_format
#         context['taux_marge_format'] = taux_marge_format
#         context['resultat_format'] = resultat_format
#         context['totl_piece_format'] = totl_piece_format
#         return context


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
    pieces = Piece.objects.filter(quantite__gt=0)
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



@user_passes_test(is_caissier, is_admin_magasin)
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
    print("++++++++++++++++++++++++++++",commande.panier,'\n')
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

#scanne 
from django.shortcuts import render, get_object_or_404
from .models import Commande

def details_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    return render(request, 'details_commande.html', {'commande': commande})

def scanner_qr_code(request):
    return render(request, 'scanner.html')
