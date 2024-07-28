from django.urls import path
from .views import piece_list, piece_detail, piece_create, piece_update, piece_delete

urlpatterns = [
    path('pieces/', piece_list, name='piece_list'),
    path('pieces/<int:pk>/', piece_detail, name='piece_detail'),
    path('pieces/new/', piece_create, name='piece_create'),
    path('pieces/<int:pk>/edit/', piece_update, name='piece_update'),
    path('pieces/<int:pk>/delete/', piece_delete, name='piece_delete'),
]
