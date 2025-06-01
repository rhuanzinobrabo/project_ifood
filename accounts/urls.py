from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.myAccount, name='myAccount'),
    path('request-otp/', views.request_otp, name='request_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('criarUsuario/', views.registerUser, name='registerUser'),
    path('criarRestaurante/', views.registerVendor, name='registerVendor'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('minhaConta/', views.myAccount, name='myAccount'),
    path('perfil/', views.edit_profile, name='edit_profile'),
    path('custDashboard/', views.custDashboard, name='custDashboard'),
    path('vendorDashboard/', views.vendorDashboard, name='vendorDashboard'),
    path('meu-restaurante/', views.restaurant_profile, name='restaurant_profile'),
    path('restaurante/', include('vendor.urls')),  # Inclui rotas do app vendor
    path('choose-account/', views.choose_account_type, name='choose_account_type'),
    path('conta/cadastrar/', views.complete_profile, name='complete_profile'),
]
