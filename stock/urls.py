from django.urls import path
from .views import caisseDashboard,livraison_accueil, piece_list, piece_detail, piece_update, piece_delete,ajouter_au_panier, valider_livraison, valider_paiement, valider_panier,accueil,base,livraison_dashboard,panier,supprimer_du_panier,retirer_du_cart,generate_receipt

# from . import views
from .views import *
from . import views
urlpatterns = [
    path('admin_magasin', DashboardView.as_view(), name='adminmagasin'),
    #piece
    path('piece_accueil/', piece_list, name='piece_list_accueil'),
    path('piece/<int:pk>/',piece_detail, name='piece_detail'),
    path('piece/new/',piece_create, name='piece_create'),
    path('create_fournisseur',AddfournisseurView.as_view(), name='fournisseur'),
    path('update_fournisseur/<int:pk>/edit',UpdatefournisseurView.as_view(), name='update_fournisseur'),
    path('update_fournisseur/<int:pk>/delete',DeletFournisseurView.as_view(), name='delet_fournisseur'),
    path('piece/<int:pk>/edit/',piece_update, name='piece_update'),
    path('piece/<int:pk>/delete/', piece_delete, name='piece_delete'),
    #panier
    path('panier/ajouter/<int:piece_id>/', ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/', panier, name='panier'),
    path('panier/valider/', valider_panier, name='valider_panier'),
    path('panier/supprimer/<int:item_id>/', supprimer_du_panier, name='supprimer_du_panier'),
    path('panier/remove/<int:piece_id>/', retirer_du_cart, name='retirer_du_panier'),
    #VUE caisse
    
    path('caissier/dashboard/', caisseDashboard, name='caisseDashboard'),
    path('caissier/valider/<str:ticket_id>/', valider_paiement, name='valider_paiement'),
    #VUE livraison
    path('livraison/', livraison_accueil, name='livraison_accueil'), #bienvenue
    path('livraison/dashboard/', livraison_dashboard, name='livraison_dashboard'),
    path('livraison/valider/<str:ticket_id>/', valider_livraison, name='valider_livraison'),
    #pour acceuil (Client)
    path('acceuil/', accueil, name='accueil'),
    #reçu
    path('recu/commande/<int:commande_id>/', generate_receipt, name='generate_receipt'),
    #scanne
    path('details_commande/<int:commande_id>/', views.details_commande, name='details_commande'),
    path('scanner/', views.scanner_qr_code, name='scanner_qr_code'),

    
]
                                    # <script>
                                    # function printReceipt(orderId) {
                                    #      var url = 'recu/commande/' + commande_id + '/'; 
                                    #      var printWindow = window.open(url, 'Print', 'width=800,height=600');
                                    #      printWindow.onload = function() {
                                    #          printWindow.print();
                                    #      };
                                    #  }
                                                                        
                                    # </script>