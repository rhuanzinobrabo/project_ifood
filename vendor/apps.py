"""
Arquivo: vendor/apps.py
Descrição: Configuração do aplicativo vendor no Django.
Define o nome do aplicativo e o campo de chave primária padrão.

Dependências principais:
- Django AppConfig: Configuração base para aplicativos Django
"""

# Imports do Django
from django.apps import AppConfig


class VendorConfig(AppConfig):
    """
    Configuração do aplicativo vendor.
    
    Define configurações básicas como o campo de chave primária padrão
    e o nome do aplicativo no sistema.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vendor'
