from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.defaultfilters import slugify

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
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    restaurants = Vendor.objects.all().order_by('-created_at')
    
    # Aplicar filtros se fornecidos
    if search_query:
        restaurants = restaurants.filter(
            Q(vendor_name__icontains=search_query) | 
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    if status_filter:
        is_approved = status_filter == 'approved'
        restaurants = restaurants.filter(is_approved=is_approved)
    
    # Paginação
    paginator = Paginator(restaurants, 10)  # 10 restaurantes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'restaurants': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
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
            
            # Obter usuário e perfil do formulário
            user_id = request.POST.get('user')
            try:
                from accounts.models import User
                user = User.objects.get(id=user_id)
                user_profile = UserProfile.objects.get(user=user)
                
                # Verificar se o usuário já tem um restaurante
                if Vendor.objects.filter(user=user).exists():
                    messages.error(request, 'Este usuário já possui um restaurante cadastrado.')
                    return redirect('restaurant_create')
                
                # Configurar o restaurante
                vendor.user = user
                vendor.user_profile = user_profile
                vendor.vendor_slug = slugify(vendor.vendor_name)
                vendor.save()
                
                messages.success(request, f'Restaurante {vendor.vendor_name} criado com sucesso!')
                return redirect('restaurant_detail', pk=vendor.pk)
            except Exception as e:
                messages.error(request, f'Erro ao criar restaurante: {str(e)}')
                return redirect('restaurant_create')
    else:
        form = VendorForm()
        
        # Obter usuários que podem ser restaurantes (role=1)
        from accounts.models import User
        users = User.objects.filter(role=1)
    
    context = {
        'form': form,
        'users': users,
    }
    return render(request, 'vendor/restaurant_create.html', context)

@login_required(login_url='social_login')
def restaurant_detail(request, pk):
    """
    Exibe detalhes de um restaurante (Create - Read - UPDATE - Delete)
    """
    restaurant = get_object_or_404(Vendor, pk=pk)
    
    # Verificar permissão (admin ou dono do restaurante)
    if not request.user.is_superuser and request.user != restaurant.user:
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('myAccount')
    
    context = {
        'restaurant': restaurant,
    }
    return render(request, 'vendor/restaurant_detail.html', context)

@login_required(login_url='social_login')
def restaurant_update(request, pk):
    """
    Atualiza um restaurante existente (Create - Read - Update - DELETE)
    """
    restaurant = get_object_or_404(Vendor, pk=pk)
    
    # Verificar permissão (admin ou dono do restaurante)
    if not request.user.is_superuser and request.user != restaurant.user:
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('myAccount')
    
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            vendor = form.save(commit=False)
            
            # Atualizar status de aprovação (apenas admin)
            if request.user.is_superuser:
                is_approved = request.POST.get('is_approved') == 'on'
                vendor.is_approved = is_approved
            
            # Atualizar slug se o nome mudou
            if vendor.vendor_name != restaurant.vendor_name:
                vendor.vendor_slug = slugify(vendor.vendor_name)
                
            vendor.save()
            
            messages.success(request, f'Restaurante {vendor.vendor_name} atualizado com sucesso!')
            return redirect('restaurant_detail', pk=vendor.pk)
    else:
        form = VendorForm(instance=restaurant)
    
    context = {
        'form': form,
        'restaurant': restaurant,
    }
    return render(request, 'vendor/restaurant_update.html', context)

@login_required(login_url='social_login')
def restaurant_delete(request, pk):
    """
    Exclui um restaurante (Create - Read - Update - DELETE)
    """
    restaurant = get_object_or_404(Vendor, pk=pk)
    
    # Verificar permissão (apenas admin pode excluir)
    if not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para excluir restaurantes.')
        return redirect('myAccount')
    
    if request.method == 'POST':
        restaurant_name = restaurant.vendor_name
        restaurant.delete()
        messages.success(request, f'Restaurante {restaurant_name} excluído com sucesso!')
        return redirect('restaurant_list')
    
    context = {
        'restaurant': restaurant,
    }
    return render(request, 'vendor/restaurant_delete.html', context)

# --- Dashboard do Restaurante ---

@login_required(login_url='social_login')
@user_passes_test(check_role_vendor)
def restaurant_dashboard(request):
    """
    Dashboard do restaurante para o proprietário
    """
    vendor = get_object_or_404(Vendor, user=request.user)
    
    context = {
        'vendor': vendor,
        # Adicionar estatísticas e outras informações relevantes
    }
    return render(request, 'vendor/restaurant_dashboard.html', context)

# --- Perfil do Restaurante ---

@login_required(login_url='social_login')
@user_passes_test(check_role_vendor)
def restaurant_profile(request):
    """
    Perfil do restaurante para o proprietário
    """
    vendor = get_object_or_404(Vendor, user=request.user)
    
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            vendor = form.save(commit=False)
            
            # Atualizar slug se o nome mudou
            if vendor.vendor_name != vendor.vendor_name:
                vendor.vendor_slug = slugify(vendor.vendor_name)
                
            vendor.save()
            
            messages.success(request, 'Perfil do restaurante atualizado com sucesso!')
            return redirect('restaurant_profile')
    else:
        form = VendorForm(instance=vendor)
    
    context = {
        'form': form,
        'vendor': vendor,
        'profile': vendor.user_profile,
    }
    return render(request, 'vendor/restaurant_profile.html', context)
