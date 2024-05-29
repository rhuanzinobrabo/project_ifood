from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.myAccount),
    path('criarUsuario/', views.registerUser, name='registerUser'),
    path('criarRestaurante/', views.registerVendor, name='registerVendor'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('minhaConta/', views.myAccount, name='myAccount'),
    path('clienteDashboard/', views.custDashboard, name='custDashboard'),
    path('restauranteDashboard/', views.vendorDashboard, name='vendorDashboard'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('esqueci_minhasenha/', views.forgot_password, name='forgot_password'),
    path('reset_password_validate/<uidb64>/<token>/', views.reset_password_validate, name='reset_password_validate'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('restaurante/', include('vendor.urls'))
]