from django import forms
from .models import *

class VendorForm(forms.ModelForm):
    vendor_license = forms.ImageField(widget=forms.FileInput(attrs={'class':'info-restaurante'}))
    class Meta: 
        model = Vendor
        fields = ['vendor_name', 'vendor_license']

        