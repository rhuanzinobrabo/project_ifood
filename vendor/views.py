"""
Arquivo: vendor/views.py
Descrição: Contém todas as views relacionadas ao gerenciamento de restaurantes, incluindo:
- CRUD completo de restaurantes
- Aprovação e gerenciamento de status
- Visualização de detalhes e listagens

Dependências principais:
- vendor/models.py: Modelo de restaurante (Vendor)
- vendor/forms.py: Formulários para manipulação de dados de restaurantes
- accounts/models.py: Modelos de usuário e perfil
- accounts/views.py: Funções de verificação de papel do usuário
"""

# Imports do Django
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.defaultfilters import slugify

# Imports locais (do próprio projeto)
from accounts.models import UserProfile
from accounts.views import check_role_admin, check_role_vendor
from .models import Vendor
from .forms import VendorForm

# --- CRUD de Restaurantes ---

@login_required(login_url='social_login')
@user_passes_test(check_role_admin)
def restaurant_list(request):
    """
    Lista todos os restaurantes (CREATE - Read - Update - Delete)
    """
    # Busca e filtros
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    
    restaurants = Vendor.objects.all().order_by('-created_at')
    
    # Filtro por nome ou email
    if query:
        restaurants = restaurants.filter(
            Q(vendor_name__icontains=query) | 
            Q(user__email__icontains=query)
        )
    
    # Filtro por status de aprovação
    if status == 'approved':
        restaurants = restaurants.filter(is_approved=True)
    elif status == 'pending':
        restaurants = restaurants.filter(is_approved=False)
    
    # Paginação
    paginator = Paginator(restaurants, 10)  # 10 restaurantes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'restaurants': page_obj,
        'query': query,
        'status': status,
    }
    return render(request, 'vendor/restaurant_list.html', context)


@login_required(login_url='social_login')
@user_passes_test(check_role_admin)
def restaurant_create(request):
    """
    Cria um novo restaurante (Create - READ - Update - Delete)
    """
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save(commit=False)
            
            # Gerar slug a partir do nome do restaurante
            vendor.vendor_slug = slugify(vendor.vendor_name)
            
            # Salvar o restaurante
            vendor.save()
            
            messages.success(request, 'Restaurante criado com sucesso!')
            return redirect('restaurant_list')
        else:
            messages.error(request, 'Erro ao criar restaurante. Por favor, corrija os erros abaixo.')
    else:
        form = VendorForm()
    
    context = {
        'form': form,
    }
    return render(request, 'vendor/restaurant_create.html', context)


@login_required(login_url='social_login')
@user_passes_test(check_role_admin)
def restaurant_detail(request, pk=None):
    """
    Exibe detalhes de um restaurante específico (Create - Read - UPDATE - Delete)
    """
    restaurant = get_object_or_404(Vendor, pk=pk)
    
    context = {
        'restaurant': restaurant,
    }
    return render(request, 'vendor/restaurant_detail.html', context)


@login_required(login_url='social_login')
@user_passes_test(check_role_admin)
def restaurant_update(request, pk=None):
    """
    Atualiza um restaurante existente (Create - Read - Update - DELETE)
    """
    restaurant = get_object_or_404(Vendor, pk=pk)
    
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            vendor = form.save(commit=False)
            
            # Gerar slug a partir do nome do restaurante
            vendor.vendor_slug = slugify(vendor.vendor_name)
            
            # Salvar o restaurante
            vendor.save()
            
            messages.success(request, 'Restaurante atualizado com sucesso!')
            return redirect('restaurant_detail', pk=vendor.pk)
        else:
            messages.error(request, 'Erro ao atualizar restaurante. Por favor, corrija os erros abaixo.')
    else:
        form = VendorForm(instance=restaurant)
    
    context = {
        'form': form,
        'restaurant': restaurant,
    }
    return render(request, 'vendor/restaurant_update.html', context)


@login_required(login_url='social_login')
@user_passes_test(check_role_admin)
def restaurant_delete(request, pk=None):
    """
    Exclui um restaurante (Create - Read - Update - Delete)
    """
    restaurant = get_object_or_404(Vendor, pk=pk)
    
    if request.method == 'POST':
        restaurant.delete()
        messages.success(request, 'Restaurante excluído com sucesso!')
        return redirect('restaurant_list')
    
    context = {
        'restaurant': restaurant,
    }
    return render(request, 'vendor/restaurant_delete.html', context)


@login_required(login_url='social_login')
@user_passes_test(check_role_admin)
def approve_restaurant(request, pk=None):
    """
    Aprova um restaurante pendente
    """
    restaurant = get_object_or_404(Vendor, pk=pk)
    restaurant.is_approved = True
    restaurant.save()
    
    messages.success(request, f'O restaurante {restaurant.vendor_name} foi aprovado com sucesso!')
    return redirect('restaurant_list')


@login_required(login_url='social_login')
@user_passes_test(check_role_admin)
def disapprove_restaurant(request, pk=None):
    """
    Desaprova um restaurante aprovado
    """
    restaurant = get_object_or_404(Vendor, pk=pk)
    restaurant.is_approved = False
    restaurant.save()
    
    messages.success(request, f'O restaurante {restaurant.vendor_name} foi desaprovado com sucesso!')
    return redirect('restaurant_list')
