from django.urls import path
from . import views

urlpatterns = [
    # CRUD de Restaurantes
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurants/create/', views.restaurant_create, name='restaurant_create'),
    path('restaurants/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('restaurants/<int:pk>/update/', views.restaurant_update, name='restaurant_update'),
    path('restaurants/<int:pk>/delete/', views.restaurant_delete, name='restaurant_delete'),
    
    # Dashboard e Perfil do Restaurante
    path('dashboard/', views.restaurant_dashboard, name='restaurant_dashboard'),
    path('profile/', views.restaurant_profile, name='restaurant_profile'),
]
