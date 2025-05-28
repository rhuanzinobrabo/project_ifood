"""
Arquivo: vendor/admin.py
Descrição: Configuração da interface administrativa para o modelo Vendor (restaurante),
permitindo gerenciamento de restaurantes através do painel admin do Django.
Inclui customizações para exibição, filtragem e edição de restaurantes.

Dependências principais:
- vendor/models.py: Modelo Vendor (restaurante)
"""

# Imports do Django
from django.contrib import admin

# Imports locais (do próprio projeto)
from vendor.models import Vendor


class VendorAdmin(admin.ModelAdmin):
    """
    Customização da interface administrativa para o modelo Vendor.
    
    Configura quais campos são exibidos na listagem, quais são clicáveis
    e quais podem ser editados diretamente na listagem.
    """
    list_display = ('user', 'vendor_name', 'is_approved', 'created_at')
    list_display_links = ('user', 'vendor_name')
    list_editable = ('is_approved',)


# Registra o modelo no admin
admin.site.register(Vendor, VendorAdmin)
