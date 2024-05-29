from django import forms
from .models import User, UserProfile

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

        
    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                'As senhas não coincidem.'
                )
        
class UserProfileForm(forms.ModelForm):
    address_line_1 = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Escreva aqui...', 'required': 'required'}))
    profile_picture = forms.ImageField(widget=forms.FileInput(attrs={'class':'info-restaurante'}))
    cover_photo = forms.ImageField(widget=forms.FileInput(attrs={'class':'btn btn-info'}))

    # latitude = forms.ImageField(widget=forms.TextInput(attrs={'readonly':'readonly'}))
    # longitude = forms.ImageField(widget=forms.TextInput(attrs={'readonly':'readonly'}))

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'cover_photo', 'address_line_1', 'country', 'state', 'city', 'pin_code', 'latitude', 'longitude']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field == 'latitude' or field == 'longitude':
                self.fields[field].widget.attrs['readonly'] = 'readonly'