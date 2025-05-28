"""
Arquivo: accounts/admin.py
Descrição: Configuração da interface administrativa para os modelos de usuário,
permitindo gerenciamento de usuários e perfis através do painel admin do Django.
Inclui customizações para exibição, filtragem e edição de usuários.

Dependências principais:
- accounts/models.py: Modelos User e UserProfile
"""

# Imports do Django
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Imports locais (do próprio projeto)
from .models import User, UserProfile

class UserAdmin(BaseUserAdmin):
    """
    Customização da interface administrativa para o modelo User.
    
    Configura quais campos são exibidos na listagem, quais filtros estão disponíveis,
    e como os formulários de criação e edição são organizados.
    """
    list_display = ('email', 'phone_number', 'username', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'username', 'phone_number', 'role')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('date_joined',)}),  # 🔧 Removido 'last_login'
    )

    readonly_fields = ('last_login',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )

    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

# Registra os modelos no admin
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
