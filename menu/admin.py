"""
Arquivo: menu/admin.py
Descrição: Configuração da interface administrativa para os modelos do cardápio,
permitindo gerenciamento de categorias e itens de comida através do painel admin do Django.
Inclui customizações para exibição, filtragem e edição de itens do cardápio.

Dependências principais:
- menu/models.py: Modelos Category e FoodItem
"""

# Imports do Django
from django.contrib import admin

# Imports locais (do próprio projeto)
from menu.models import Category, FoodItem


class CategoryAdmin(admin.ModelAdmin):
    """
    Customização da interface administrativa para o modelo Category.
    
    Configura campos pré-populados, campos de busca e exibição na listagem
    para facilitar o gerenciamento de categorias de alimentos.
    """
    prepopulated_fields = {'slug': ('category_name',)}
    search_fields = ('category_name', 'vendor__vendor_name')
    list_display = ('category_name', 'vendor', 'updated_at')


class FoodItemAdmin(admin.ModelAdmin):
    """
    Customização da interface administrativa para o modelo FoodItem.
    
    Configura campos pré-populados, campos de busca, filtros e exibição na listagem
    para facilitar o gerenciamento de itens de comida.
    """
    prepopulated_fields = {'slug': ('food_title',)}
    list_display = ('food_title', 'vendor', 'price', 'is_available', 'updated_at')
    search_fields = ('food_title', 'category__category_name', 'vendor__vendor_name', 'price')
    list_filter = ('is_available',)


# Registra os modelos no admin
admin.site.register(Category, CategoryAdmin)
admin.site.register(FoodItem, FoodItemAdmin)
