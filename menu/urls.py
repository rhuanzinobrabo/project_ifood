from django.urls import path
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
