from django.urls import path


from .views import caisse_dashboard, caissier_accueil, livraison_accueil, piece_list, piece_detail, piece_create, piece_update, piece_delete,ajouter_au_panier,panier_detail, valider_livraison, valider_paiement, valider_panier,accueil,base,admin_magasin

urlpatterns = [
    
    path('admin_magasin/', admin_magasin, name='adminmagasin'),
    path('b/', base, name='bb'),
    path('piece/', piece_list, name='piece_list'),
    path('piece/<int:pk>/',piece_detail, name='piece_detail'),
    path('piece/new/',piece_create, name='piece_create'),
    path('piece/<int:pk>/edit/',piece_update, name='piece_update'),
    path('piece/<int:pk>/delete/', piece_delete, name='piece_delete'),
    path('panier/ajouter/', ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/', panier_detail, name='panier_detail'),
    path('panier/valider/', valider_panier, name='valider_panier'),
    path('caissier/', caissier_accueil, name='caissier_accueil'),
    path('caissier/valider/<str:ticket_id>/', valider_paiement, name='valider_paiement'),
    path('livraison/', livraison_accueil, name='livraison_accueil'),
     path('acceuil/', accueil, name='accueil'),
    path('livraison/valider/<str:ticket_id>/', valider_livraison, name='valider_livraison'),
    path('caisse/dashboard/', caisse_dashboard, name='caisse_dashboard'),
]
