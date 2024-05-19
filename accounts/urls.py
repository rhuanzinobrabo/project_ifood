from django.urls import path
from . import views

urlpatterns = [
    path('criarUsuario/', views.registerUser, name='registerUser'),
    path('criarRestaurante/', views.registerVendor, name='registerVendor'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('minhaConta/', views.myAccount, name='myAccount'),
    path('clienteDashboard/', views.custDashboard, name='custDashboard'),
    path('RestauranteDashboard/', views.vendorDashboard, name='vendorDashboard'),
    path('activate/<uidb64>/<token>', views.activate, name='activate')
]