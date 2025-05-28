"""
Arquivo: accounts/apps.py
Descrição: Configuração do aplicativo accounts no Django.
Define o nome do aplicativo, campo de chave primária padrão e
inicializa os sinais quando o aplicativo é carregado.

Dependências principais:
- accounts/signals.py: Sinais para automação de tarefas relacionadas a usuários
"""

# Imports do Django
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Configuração do aplicativo accounts.
    
    Define configurações básicas e inicializa os sinais quando o aplicativo é carregado.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """
        Método chamado quando o aplicativo está pronto.
        
        Importa os sinais para garantir que sejam registrados corretamente.
        """
        # Importa os sinais apenas quando o app estiver pronto
        import accounts.signals  # noqa
