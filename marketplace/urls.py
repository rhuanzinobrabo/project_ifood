"""
Arquivo: marketplace/urls.py
Descrição: Define todas as rotas (URLs) do aplicativo marketplace, incluindo:
- Rotas para listagem e busca de restaurantes e produtos
- Rotas para gerenciamento de carrinho
- Rotas para checkout e processamento de pedidos
- Rotas para geração e visualização de notas fiscais

Dependências principais:
- marketplace/views.py: Views principais do marketplace
- marketplace/views_*.py: Views auxiliares para funcionalidades específicas
"""

# Imports do Django
from django.urls import path

# Imports locais (do próprio projeto)
from . import views

urlpatterns = [
    path('', views.marketplace, name='marketplace'),
    path('cart/', views.cart, name='cart'),
    path('add_cart/<int:food_id>/', views.add_to_cart, name='add_cart'),
    path('decrease_cart/<int:food_id>/', views.decrease_cart, name='decrease_cart'),
    path('delete_cart/<int:cart_id>/', views.delete_cart, name='delete_cart'),
    
    # Busca e filtros de restaurantes
    path('restaurants/', views.restaurant_search, name='restaurant_search'),
    path('restaurants/<int:vendor_id>/', views.restaurant_detail, name='restaurant_detail'),
    path('favorite/<int:vendor_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('favorites/', views.list_favorites, name='list_favorites'),
    
    # Busca e filtros de produtos
    path('products/', views.product_search, name='product_search'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # Checkout e pedidos
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<int:order_id>/<str:payment_method>/', views.payment, name='payment'),
    path('order-complete/<str:order_number>/', views.order_complete, name='order_complete'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-detail/<str:order_number>/', views.order_detail, name='order_detail'),
    
    # Notas fiscais
    path('invoice/<str:order_number>/', views.generate_invoice, name='generate_invoice'),
    path('view-invoice/<str:order_number>/', views.view_invoice, name='view_invoice'),
    path('my-invoices/', views.invoice_list, name='invoice_list'),
    
    # Manter as rotas existentes
    path('<slug:vendor_slug>/', views.vendor_detail, name='vendor_detail'),
    path('search/', views.search, name='search'),
]
