# vendor/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.urls import reverse # Importar reverse

from accounts.models import UserProfile # Importar UserProfile se necessário
from accounts.utils import check_role_admin, check_role_vendor
from .models import Vendor
from .forms import VendorForm

# --- CRUD de Restaurantes ---

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin, login_url='request_otp') # Adicionar login_url
def restaurant_list(request):
    if not check_role_admin(request.user):
        messages.error(request, 'Acesso restrito. Somente administradores podem acessar esta área.')
        return redirect(reverse('home'))
        
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    restaurants = Vendor.objects.all().order_by('-created_at')
    if query:
        restaurants = restaurants.filter(
            Q(vendor_name__icontains=query) | 
            Q(user__email__icontains=query)
        )
    if status == 'approved':
        restaurants = restaurants.filter(is_approved=True)
    elif status == 'pending':
        restaurants = restaurants.filter(is_approved=False)
    paginator = Paginator(restaurants, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'restaurants': page_obj,
        'query': query,
        'status': status,
    }
    return render(request, 'vendor/restaurant_list.html', context)

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin, login_url='request_otp')
def restaurant_create(request):
    if not check_role_admin(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect(reverse('home'))
        
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.vendor_slug = slugify(vendor.vendor_name)
            # Lógica para associar User/UserProfile precisa ser definida
            # Ex: Selecionar um User existente ou criar um novo
            # vendor.user = ... 
            # vendor.user_profile = ...
            vendor.save()
            messages.success(request, 'Restaurante criado com sucesso!')
            return redirect(reverse('restaurant_list'))
        else:
            messages.error(request, 'Erro ao criar restaurante. Por favor, corrija os erros abaixo.')
    else:
        form = VendorForm()
    context = {'form': form,}
    return render(request, 'vendor/restaurant_create.html', context)

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin, login_url='request_otp')
def restaurant_detail(request, pk=None):
    if not check_role_admin(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect(reverse('home'))
        
    restaurant = get_object_or_404(Vendor, pk=pk)
    context = {'restaurant': restaurant,}
    return render(request, 'vendor/restaurant_detail.html', context)

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin, login_url='request_otp')
def restaurant_update(request, pk=None):
    if not check_role_admin(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect(reverse('home'))
        
    restaurant = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.vendor_slug = slugify(vendor.vendor_name)
            vendor.save()
            messages.success(request, 'Restaurante atualizado com sucesso!')
            return redirect(reverse('restaurant_list')) 
        else:
            messages.error(request, 'Erro ao atualizar restaurante. Por favor, corrija os erros abaixo.')
    else:
        form = VendorForm(instance=restaurant)
    context = {'form': form, 'restaurant': restaurant,}
    return render(request, 'vendor/restaurant_update.html', context)

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin, login_url='request_otp')
def restaurant_delete(request, pk=None):
    if not check_role_admin(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect(reverse('home'))
        
    restaurant = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST': 
        restaurant.delete()
        messages.success(request, 'Restaurante excluído com sucesso!')
        return redirect(reverse('restaurant_list'))
    # Para GET, mostrar confirmação (template não fornecido)
    # return render(request, 'vendor/restaurant_confirm_delete.html', {'restaurant': restaurant})
    return redirect(reverse('restaurant_list')) # Redireciona se não for POST

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin, login_url='request_otp')
def approve_restaurant(request, pk=None):
    if not check_role_admin(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect(reverse('home'))
        
    restaurant = get_object_or_404(Vendor, pk=pk)
    restaurant.is_approved = True
    restaurant.save()
    messages.success(request, f'O restaurante {restaurant.vendor_name} foi aprovado com sucesso!')
    return redirect(reverse('restaurant_list'))

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin, login_url='request_otp')
def disapprove_restaurant(request, pk=None):
    if not check_role_admin(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect(reverse('home'))
        
    restaurant = get_object_or_404(Vendor, pk=pk)
    restaurant.is_approved = False
    restaurant.save()
    messages.success(request, f'O restaurante {restaurant.vendor_name} foi desaprovado com sucesso!')
    return redirect(reverse('restaurant_list'))

@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def restaurant_dashboard(request):
    if not check_role_vendor(request.user):
        messages.error(request, 'Acesso restrito.')
        return redirect(reverse('home'))
        
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        messages.error(request, 'Perfil de restaurante não encontrado.')
        return redirect(reverse('home')) 
        
    context = {'vendor': vendor,}
    # Certifique-se que 'vendor/dashboard.html' existe
    return render(request, 'vendor/dashboard.html', context)

