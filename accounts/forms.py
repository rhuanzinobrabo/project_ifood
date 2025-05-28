"""
Arquivo: accounts/forms.py
Descrição: Contém todos os formulários relacionados a contas de usuário, incluindo:
- Formulários de autenticação (login, registro)
- Formulários de perfil (edição, visualização)
- Formulários para seleção de tipo de conta
- Formulários para verificação (email, OTP)

Dependências principais:
- accounts/models.py: Modelos User e UserProfile
"""

# Imports do Django
from django import forms

# Imports locais (do próprio projeto)
from .models import User, UserProfile, UserAddress


class EmailForm(forms.Form):
    """
    Formulário para entrada de email, usado em processos de verificação
    e recuperação de senha.
    """
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu e-mail'
        })
    )


class OTPForm(forms.Form):
    """
    Formulário para entrada de código OTP (One-Time Password),
    usado no processo de verificação em duas etapas.
    """
    otp = forms.CharField(
        label='Código de Verificação',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o código enviado ao seu e-mail'
        })
    )


class UserForm(forms.ModelForm):
    """
    Formulário para criação e edição de usuários,
    com campos básicos como nome, sobrenome e tipo de conta.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primeiro nome'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Último nome'
            }),
            'role': forms.Select(attrs={
                'class': 'form-control'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Telefone'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['role'].label = "Tipo de conta"
        self.fields['role'].choices = (
            (1, 'Restaurante'),
            (2, 'Cliente'),
        )


class UserProfileForm(forms.ModelForm):
    """
    Formulário para criação e edição de perfil de usuário,
    incluindo endereço e imagens de perfil.
    """
    address_line_1 = forms.CharField(
        label='Endereço',
        widget=forms.TextInput(attrs={
            'placeholder': 'Rua, número, complemento...',
            'required': 'required',
            'class': 'form-control'
        })
    )
    profile_picture = forms.ImageField(
        label='Foto de Perfil',
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    cover_photo = forms.ImageField(
        label='Capa',
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = [
            'profile_picture', 'cover_photo', 'address_line_1', 'country',
            'state', 'city', 'latitude', 'longitude'
        ]
        # Removi o campo 'pin_code' que estava causando o erro

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            if field in ['latitude', 'longitude']:
                self.fields[field].widget.attrs['readonly'] = 'readonly'


class AccountTypeForm(forms.ModelForm):
    """
    Formulário para seleção de tipo de conta (Cliente ou Restaurante),
    usado no processo de registro.
    """
    class Meta:
        model = User
        fields = ['role']
        widgets = {
            'role': forms.RadioSelect(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super(AccountTypeForm, self).__init__(*args, **kwargs)
        self.fields['role'].label = "Tipo de conta"
        self.fields['role'].choices = (
            (1, 'Restaurante'),
            (2, 'Cliente'),
        )


class CustomerProfileForm(forms.ModelForm):
    """
    Formulário específico para perfil de cliente,
    com campos personalizados para este tipo de usuário.
    """
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Primeiro nome'
    }))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Último nome'
    }))
    phone_number = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Telefone'
    }))
    address_line_1 = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Rua, número, complemento...'
    }))

    class Meta:
        model = UserProfile
        fields = ['address_line_1', 'country', 'state', 'city', 'latitude', 'longitude']
        # Removi o campo 'pin_code'

    def __init__(self, *args, **kwargs):
        super(CustomerProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            if field in ['latitude', 'longitude']:
                self.fields[field].widget.attrs['readonly'] = 'readonly'

class RestaurantProfileForm(forms.ModelForm):
    """
    Formulário específico para perfil de restaurante,
    com campos personalizados para este tipo de usuário.
    """
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Primeiro nome'
    }))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Último nome'
    }))
    phone_number = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Telefone'
    }))
    profile_picture = forms.ImageField(required=True, widget=forms.FileInput(attrs={
        'class': 'form-control'
    }))
    cover_photo = forms.ImageField(required=True, widget=forms.FileInput(attrs={
        'class': 'form-control'
    }))
    address_line_1 = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Rua, número, complemento...'
    }))

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'cover_photo', 'address_line_1', 'country', 'state', 'city', 'latitude', 'longitude']
        # Removi o campo 'pin_code'

    def __init__(self, *args, **kwargs):
        super(RestaurantProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            if field in ['latitude', 'longitude']:
                self.fields[field].widget.attrs['readonly'] = 'readonly'


class UserAddressForm(forms.ModelForm):
    """
    Formulário para criação e edição de endereços de usuário
    """
    class Meta:
        model = UserAddress
        fields = ['address_type', 'address_line1', 'address_line2', 'city', 'state', 'country', 
                 'postal_code', 'latitude', 'longitude', 'is_default']
        exclude = ['user']
        
    def __init__(self, *args, **kwargs):
        super(UserAddressForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
        
        # Tornar alguns campos opcionais
        self.fields['address_line2'].required = False
        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
        self.fields['is_default'].widget = forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })