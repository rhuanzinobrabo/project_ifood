"""
Arquivo: menu/urls.py
Descrição: Define todas as rotas relacionadas ao gerenciamento de cardápio, incluindo:
- CRUD de categorias de alimentos
- CRUD de itens de comida
- Visualização e organização do cardápio

Dependências principais:
- menu/views.py: Views para manipulação de categorias e itens de comida
"""

# Imports do Django
from django.urls import path

# Imports locais (do próprio projeto)
from . import views

urlpatterns = [
    # CRUD de Categorias
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # CRUD de Refeições/Lanches
    path('items/', views.food_list, name='food_list'),
    path('items/create/', views.food_create, name='food_create'),
    path('items/<int:pk>/', views.food_detail, name='food_detail'),
    path('items/<int:pk>/update/', views.food_update, name='food_update'),
    path('items/<int:pk>/delete/', views.food_delete, name='food_delete'),
]
