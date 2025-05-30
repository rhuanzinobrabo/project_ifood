from django.shortcuts import render
from django.http import HttpResponse
from vendor.models import Vendor

def home(request):
    # Removido filtro de aprovação e status do usuário para exibir todos os restaurantes cadastrados
    vendors = Vendor.objects.all()[:8]
    context = {
        'vendors': vendors
    }
    return render(request, 'home.html', context)