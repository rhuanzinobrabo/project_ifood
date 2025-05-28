"""
Arquivo: marketplace/admin.py
Descrição: Configuração da interface administrativa para os modelos do marketplace,
permitindo gerenciamento de carrinhos de compra e taxas através do painel admin do Django.
Inclui customizações para exibição, filtragem e edição de registros.

Dependências principais:
- marketplace/models.py: Modelos Cart e Tax
"""

# Imports do Django
from django.contrib import admin

# Imports locais (do próprio projeto)
from .models import Cart, Tax


class CartAdmin(admin.ModelAdmin):
    """
    Customização da interface administrativa para o modelo Cart.
    
    Configura quais campos são exibidos na listagem e como são organizados,
    facilitando o gerenciamento de itens no carrinho de compras.
    """
    list_display = ('user', 'fooditem', 'quantity', 'updated_at')


class TaxAdmin(admin.ModelAdmin):
    """
    Customização da interface administrativa para o modelo Tax.
    
    Configura quais campos são exibidos na listagem, permitindo
    visualizar e gerenciar facilmente as taxas aplicáveis aos pedidos.
    """
    list_display = ('tax_type', 'tax_percentage', 'is_active')


# Registra os modelos no admin
admin.site.register(Cart, CartAdmin)
admin.site.register(Tax, TaxAdmin)
