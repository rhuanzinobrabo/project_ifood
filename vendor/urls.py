from django.urls import path, include
from . import views
from accounts import views as AccountViews

urlpatterns = [
    path('', AccountViews.vendorDashboard, name='vendor'),
    path('perfil/', views.vprofile, name='vprofile'),
    path('cardapio/', views.menu_builder, name='menu_builder'),
    path('cardapio/categoria/<int:pk>/', views.fooditems_by_category, name='fooditems_by_category'),
    path('cardapio/categoria/adicionar/', views.add_category, name='add_category'),
    path('cardapio/categoria/editar/<int:pk>', views.edit_category, name='edit_category'),
    path('cardapio/categoria/apagar/<int:pk>', views.delete_category, name='delete_category'),
    path('cardapio/prato/add/', views.add_food, name='add_food'),
    path('cardapio/prato/apagar/<int:pk>', views.delete_food, name='delete_food'),
]