"""
Arquivo: accounts/urls.py
Descrição: Define todas as rotas relacionadas a contas de usuário, incluindo:
- Autenticação (login, registro, logout)
- Dashboards específicos por tipo de usuário
- Gerenciamento de perfil
- Administração de usuários
- Gerenciamento de endereços

Dependências principais:
- accounts/views.py: Views para manipulação de contas de usuário
- accounts/address_views.py: Views para manipulação de endereços
"""

# Imports do Django
from django.urls import path, include

# Imports locais (do próprio projeto)
from . import views
from . import address_views

urlpatterns = [
    path('', views.myAccount, name='myAccount'),
    path('request-otp/', views.request_otp, name='request_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('criarUsuario/', views.registerUser, name='registerUser'),
    path('criarRestaurante/', views.registerVendor, name='registerVendor'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('minhaConta/', views.myAccount, name='myAccount'),
    path('custDashboard/', views.custDashboard, name='custDashboard'),
    path('vendorDashboard/', views.vendorDashboard, name='vendorDashboard'),
    path('restaurante/', include('vendor.urls')),  # Inclui rotas do app vendor
    path('choose-account/', views.choose_account_type, name='choose_account_type'),
    path('conta/cadastrar/', views.complete_profile, name='complete_profile'),
    
    # CRUD de Contas (Admin)
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/create/', views.user_create, name='user_create'),
    path('admin/users/<int:pk>/', views.user_detail, name='user_detail'),
    path('admin/users/<int:pk>/update/', views.user_update, name='user_update'),
    path('admin/users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    
    # Perfil do Usuário (Self-service)
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/delete/', views.profile_delete, name='profile_delete'),
    
    # Autenticação Social
    path('social-login/', views.social_login, name='social_login'),
    path('social-callback/', views.social_callback, name='social_callback'),
    
    # CRUD de Endereços
    path('addresses/', address_views.address_list, name='address_list'),
    path('addresses/create/', address_views.address_create, name='address_create'),
    path('addresses/<int:pk>/update/', address_views.address_update, name='address_update'),
    path('addresses/<int:pk>/delete/', address_views.address_delete, name='address_delete'),
    path('addresses/<int:pk>/set-default/', address_views.set_default_address, name='set_default_address'),
]
