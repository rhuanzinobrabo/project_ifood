from django import forms
from .models import User, UserProfile, UserAddress


class EmailForm(forms.Form):
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu e-mail'
        })
    )


class OTPForm(forms.Form):
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
            'state', 'city', 'pin_code', 'latitude', 'longitude'
        ]

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            if field in ['latitude', 'longitude']:
                self.fields[field].widget.attrs['readonly'] = 'readonly'


class AccountTypeForm(forms.ModelForm):
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

class UserAddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = ['address_type', 'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'is_default']
        widgets = {
            'address_type': forms.Select(attrs={'class': 'form-control'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua, número'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Complemento, apartamento'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Estado'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CEP'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'País'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CustomerProfileForm(forms.ModelForm):
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
        fields = ['address_line_1', 'country', 'state', 'city', 'pin_code', 'latitude', 'longitude']

    def __init__(self, *args, **kwargs):
        super(CustomerProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            if field in ['latitude', 'longitude']:
                self.fields[field].widget.attrs['readonly'] = 'readonly'


class RestaurantProfileForm(forms.ModelForm):
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
        fields = ['profile_picture', 'cover_photo', 'address_line_1', 'country', 'state', 'city', 'pin_code', 'latitude', 'longitude']

    def __init__(self, *args, **kwargs):
        super(RestaurantProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            if field in ['latitude', 'longitude']:
                self.fields[field].widget.attrs['readonly'] = 'readonly'
