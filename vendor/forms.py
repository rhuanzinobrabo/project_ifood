"""
Arquivo: vendor/forms.py
Descrição: Contém formulários para manipulação de dados de restaurantes,
permitindo criação e edição de restaurantes através da interface web.

Dependências principais:
- vendor/models.py: Modelo Vendor (restaurante)
"""

# Imports do Django
from django import forms

# Imports locais (do próprio projeto)
from .models import Vendor


class VendorForm(forms.ModelForm):
    """
    Formulário para criação e edição de restaurantes.
    
    Configura os campos disponíveis para edição e seus widgets,
    aplicando classes CSS para estilização consistente.
    """
    class Meta:
        model = Vendor
        fields = ['vendor_name', 'vendor_license']
        widgets = {
            'vendor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Restaurante'}),
            'vendor_license': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializa o formulário e aplica classes CSS aos campos.
        
        Garante que todos os campos (exceto os de upload de arquivo)
        recebam a classe 'form-control' para estilização consistente.
        """
        super(VendorForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ != 'FileInput':
                field.widget.attrs['class'] = 'form-control'
