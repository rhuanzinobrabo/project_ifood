"""
Arquivo: menu/forms.py
Descrição: Contém formulários para manipulação de dados do cardápio,
permitindo criação e edição de categorias e itens de comida através da interface web.

Dependências principais:
- menu/models.py: Modelos Category e FoodItem
"""

# Imports do Django
from django import forms

# Imports locais (do próprio projeto)
from .models import Category, FoodItem


class CategoryForm(forms.ModelForm):
    """
    Formulário para criação e edição de categorias de alimentos.
    
    Permite que restaurantes criem e editem categorias para organizar
    seus itens de comida no cardápio.
    """
    class Meta:
        model = Category
        fields = ['category_name', 'description']


class FoodItemForm(forms.ModelForm):
    """
    Formulário para criação e edição de itens de comida.
    
    Permite que restaurantes criem e editem itens específicos de comida
    com detalhes como preço, descrição e imagem.
    """
    class Meta:
        model = FoodItem
        fields = ['category', 'food_title', 'description', 'price', 'image', 'is_available']
