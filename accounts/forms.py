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
    # Campos ocultos para latitude e longitude
    latitude = forms.CharField(required=False, widget=forms.HiddenInput())
    longitude = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = UserProfile
        fields = [
            'profile_picture', 'cover_photo', 'address_line_1', 'country',
            'state', 'city', 'pin_code', 'latitude', 'longitude'
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
        # Garantir que latitude e longitude sejam sempre string vazia
        self.cleaned_data['latitude'] = ''
        self.cleaned_data['longitude'] = ''
        return self.cleaned_data


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
    # Campos ocultos para latitude e longitude
    latitude = forms.CharField(required=False, widget=forms.HiddenInput())
    longitude = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = UserProfile
        fields = ['address_line_1', 'country', 'state', 'city', 'pin_code', 'latitude', 'longitude']

    def __init__(self, *args, **kwargs):
        super(CustomerProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['latitude', 'longitude']:
                self.fields[field].widget.attrs['class'] = 'form-control'
                
        # Tradução dos labels para português
        self.fields['address_line_1'].label = 'Endereço'
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
        # Garantir que latitude e longitude sejam sempre string vazia
        self.cleaned_data['latitude'] = ''
        self.cleaned_data['longitude'] = ''
        return self.cleaned_data


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
    vendor_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nome do Restaurante'
    }))
    is_open = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input',
        'data-toggle': 'toggle',
        'data-on': 'Aberto',
        'data-off': 'Fechado',
        'data-onstyle': 'success',
        'data-offstyle': 'danger'
    }))
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'form-control'
    }))
    cover_photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'form-control'
    }))
    address_line_1 = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Rua, número, complemento...'
    }))
    # Campos ocultos para latitude e longitude
    latitude = forms.CharField(required=False, widget=forms.HiddenInput())
    longitude = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'cover_photo', 'address_line_1', 'country', 'state', 'city', 'pin_code', 'latitude', 'longitude']

    def __init__(self, *args, **kwargs):
        super(RestaurantProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['latitude', 'longitude']:
                self.fields[field].widget.attrs['class'] = 'form-control'
                
        # Tradução dos labels para português
        self.fields['profile_picture'].label = 'Foto de Perfil'
        self.fields['cover_photo'].label = 'Foto de Capa'
        self.fields['address_line_1'].label = 'Endereço'
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
        # Garantir que latitude e longitude sejam sempre string vazia
        self.cleaned_data['latitude'] = ''
        self.cleaned_data['longitude'] = ''
        return self.cleaned_data
