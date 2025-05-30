"""
Arquivo: vendor/urls.py
Descrição: Define todas as rotas relacionadas ao gerenciamento de restaurantes, incluindo:
- CRUD completo de restaurantes
- Dashboard e perfil do restaurante
- Aprovação e gerenciamento de status

Dependências principais:
- vendor/views.py: Views para manipulação de restaurantes
"""

# Imports do Django
from django.urls import path

# Imports locais (do próprio projeto)
from . import views

urlpatterns = [
    # CRUD de Restaurantes
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurants/create/', views.restaurant_create, name='restaurant_create'),
    path('restaurants/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('restaurants/<int:pk>/update/', views.restaurant_update, name='restaurant_update'),
    path('restaurants/<int:pk>/delete/', views.restaurant_delete, name='restaurant_delete'),
    
    # Dashboard do Restaurante
    path('dashboard/', views.restaurant_dashboard, name='restaurant_dashboard'),
]
