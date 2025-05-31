from django import forms
from .models import User, UserProfile


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
        # Removido 'role' pois não deve ser editado aqui
        fields = ['first_name', 'last_name', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primeiro nome'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Último nome'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Telefone'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        # Labels em português
        self.fields['first_name'].label = 'Nome'
        self.fields['last_name'].label = 'Sobrenome'
        self.fields['phone_number'].label = 'Telefone'


class UserProfileForm(forms.ModelForm):
    address_line_1 = forms.CharField(
        label='Endereço',
        widget=forms.TextInput(attrs={
            'placeholder': 'Rua, número, complemento...',
            # Removido 'required' para evitar problemas se o campo for opcional no modelo
            'class': 'form-control'
        })
    )
    # Campos ocultos para latitude e longitude
    latitude = forms.CharField(required=False, widget=forms.HiddenInput())
    longitude = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = UserProfile
        # Removido 'profile_picture' e 'cover_photo'
        fields = [
            'address_line_1', 'country', 'state', 'city', 'pin_code',
            'latitude', 'longitude'
        ]

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['latitude', 'longitude']:
                self.fields[field].widget.attrs['class'] = 'form-control'

        # Tradução dos labels para português
        self.fields['country'].label = 'País'
        self.fields['state'].label = 'Estado'
        self.fields['city'].label = 'Cidade'
        self.fields['pin_code'].label = 'CEP'

        # Placeholders em português
        self.fields['country'].widget.attrs['placeholder'] = 'País'
        self.fields['state'].widget.attrs['placeholder'] = 'Estado'
        self.fields['city'].widget.attrs['placeholder'] = 'Cidade'
        self.fields['pin_code'].widget.attrs['placeholder'] = 'CEP'

    def clean(self):
        cleaned_data = super().clean()
        # Garantir que latitude e longitude sejam sempre string vazia se não fornecidos
        cleaned_data['latitude'] = cleaned_data.get('latitude', '') or ''
        cleaned_data['longitude'] = cleaned_data.get('longitude', '') or ''
        return cleaned_data


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

# CustomerProfileForm e RestaurantProfileForm foram removidos pois UserForm e UserProfileForm são suficientes.

