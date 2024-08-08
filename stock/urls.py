from django.urls import path


from .views import caisseDashboard, caissier_accueil, livraison_accueil, piece_list, piece_detail, piece_create, piece_update, piece_delete,ajouter_au_panier, valider_livraison, valider_paiement, valider_panier,accueil,base,admin_magasin,livraison_dashboard,panier,supprimer_du_panier

urlpatterns = [
    
    path('admin_magasin/', admin_magasin, name='adminmagasin'),
    path('b/', base, name='bb'),
    #piece
    path('piece/', piece_list, name='piece_list'),
    path('piece/<int:pk>/',piece_detail, name='piece_detail'),
    path('piece/new/',piece_create, name='piece_create'),
    path('piece/<int:pk>/edit/',piece_update, name='piece_update'),
    path('piece/<int:pk>/delete/', piece_delete, name='piece_delete'),
    #panier
   path('panier/ajouter/<int:piece_id>/', ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/', panier, name='panier'),
    path('panier/valider/', valider_panier, name='valider_panier'),
    path('panier/supprimer/<int:item_id>/', supprimer_du_panier, name='supprimer_du_panier'),
    #caisse
    path('caissier/', caissier_accueil, name='caissier_accueil'),
    path('caissier/dashboard/', caisseDashboard, name='caisseDashboard'),
    path('caissier/valider/<str:ticket_id>/', valider_paiement, name='valider_paiement'),
    #livraison
    path('livraison/', livraison_accueil, name='livraison_accueil'), #bienvenue
     path('livraison/dashboard/', livraison_dashboard, name='livraison_dashboard'),
    path('livraison/valider/<str:ticket_id>/', valider_livraison, name='valider_livraison'),
    #pour acceuil (Client)
    path('acceuil/', accueil, name='accueil'),
    
]
