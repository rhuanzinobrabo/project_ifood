"""
Arquivo: accounts/context_processors.py
Descrição: Processadores de contexto para o app accounts, permitindo
que determinadas variáveis estejam disponíveis em todos os templates.
Atualmente fornece acesso ao objeto vendor do usuário logado em todos os templates.

Dependências principais:
- vendor/models.py: Modelo Vendor (restaurante)
"""

# Imports locais (do próprio projeto)
from vendor.models import Vendor

def get_vendor(request):
    """
    Processador de contexto que adiciona o objeto vendor do usuário atual ao contexto.
    
    Tenta obter o restaurante associado ao usuário atual e o disponibiliza
    para todos os templates. Se o usuário não tiver um restaurante associado
    ou não estiver autenticado, retorna None.
    
    Args:
        request: Objeto request do Django
        
    Returns:
        dict: Dicionário contendo o objeto vendor ou None
    """
    try: 
        vendor = Vendor.objects.get(user=request.user)
    except:
        vendor = None
    return dict(vendor=vendor)
