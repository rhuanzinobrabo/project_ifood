from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.defaultfilters import slugify

from accounts.views import check_role_vendor, check_role_admin
from vendor.models import Vendor
from .models import Category, FoodItem
from .forms import CategoryForm, FoodItemForm

# --- CRUD de Categorias ---

@login_required(login_url='social_login')
def category_list(request):
    """
    Lista todas as categorias do restaurante do usuário logado
    """
    if request.user.is_superuser:
        categories = Category.objects.all().order_by('-create_at')
    else:
        vendor = get_object_or_404(Vendor, user=request.user)
        categories = Category.objects.filter(vendor=vendor).order_by('-create_at')
    
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(
            Q(category_name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Paginação
    paginator = Paginator(categories, 10)  # 10 categorias por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categories': page_obj,
        'search_query': search_query,
    }
    return render(request, 'menu/category_list.html', context)

@login_required(login_url='social_login')
@user_passes_test(check_role_vendor)
def category_create(request):
    """
    Cria uma nova categoria para o restaurante do usuário logado
    """
    vendor = get_object_or_404(Vendor, user=request.user)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.vendor = vendor
            category.slug = slugify(category.category_name)
            category.save()
            
            messages.success(request, f'Categoria {category.category_name} criada com sucesso!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Criar Nova Categoria',
    }
    return render(request, 'menu/category_form.html', context)

@login_required(login_url='social_login')
def category_update(request, pk):
    """
    Atualiza uma categoria existente
    """
    category = get_object_or_404(Category, pk=pk)
    
    # Verificar permissão (admin ou dono do restaurante)
    if not request.user.is_superuser and request.user != category.vendor.user:
        messages.error(request, 'Você não tem permissão para editar esta categoria.')
        return redirect('category_list')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save(commit=False)
            category.slug = slugify(category.category_name)
            category.save()
            
            messages.success(request, f'Categoria {category.category_name} atualizada com sucesso!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': 'Editar Categoria',
    }
    return render(request, 'menu/category_form.html', context)

@login_required(login_url='social_login')
def category_delete(request, pk):
    """
    Exclui uma categoria
    """
    category = get_object_or_404(Category, pk=pk)
    
    # Verificar permissão (admin ou dono do restaurante)
    if not request.user.is_superuser and request.user != category.vendor.user:
        messages.error(request, 'Você não tem permissão para excluir esta categoria.')
        return redirect('category_list')
    
    if request.method == 'POST':
        category_name = category.category_name
        category.delete()
        messages.success(request, f'Categoria {category_name} excluída com sucesso!')
        return redirect('category_list')
    
    context = {
        'category': category,
    }
    return render(request, 'menu/category_delete.html', context)

# --- CRUD de Refeições/Lanches ---

@login_required(login_url='social_login')
def food_list(request):
    """
    Lista todas as refeições/lanches do restaurante do usuário logado
    """
    if request.user.is_superuser:
        food_items = FoodItem.objects.all().order_by('-create_at')
    else:
        vendor = get_object_or_404(Vendor, user=request.user)
        food_items = FoodItem.objects.filter(vendor=vendor).order_by('-create_at')
    
    # Filtros
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    availability_filter = request.GET.get('availability', '')
    
    if search_query:
        food_items = food_items.filter(
            Q(food_title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        food_items = food_items.filter(category_id=category_filter)
    
    if availability_filter:
        is_available = availability_filter == 'available'
        food_items = food_items.filter(is_available=is_available)
    
    # Paginação
    paginator = Paginator(food_items, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obter categorias para filtro
    if request.user.is_superuser:
        categories = Category.objects.all()
    else:
        vendor = get_object_or_404(Vendor, user=request.user)
        categories = Category.objects.filter(vendor=vendor)
    
    context = {
        'food_items': page_obj,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
        'availability_filter': availability_filter,
    }
    return render(request, 'menu/food_list.html', context)

@login_required(login_url='social_login')
@user_passes_test(check_role_vendor)
def food_create(request):
    """
    Cria uma nova refeição/lanche para o restaurante do usuário logado
    """
    vendor = get_object_or_404(Vendor, user=request.user)
    
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES)
        if form.is_valid():
            food_item = form.save(commit=False)
            food_item.vendor = vendor
            food_item.slug = slugify(food_item.food_title)
            food_item.save()
            
            messages.success(request, f'Item {food_item.food_title} criado com sucesso!')
            return redirect('food_list')
    else:
        # Filtrar categorias do restaurante do usuário
        form = FoodItemForm()
        form.fields['category'].queryset = Category.objects.filter(vendor=vendor)
    
    context = {
        'form': form,
        'title': 'Adicionar Novo Item ao Cardápio',
    }
    return render(request, 'menu/food_form.html', context)

@login_required(login_url='social_login')
def food_detail(request, pk):
    """
    Exibe detalhes de uma refeição/lanche
    """
    food_item = get_object_or_404(FoodItem, pk=pk)
    
    # Verificar permissão (admin ou dono do restaurante)
    if not request.user.is_superuser and request.user != food_item.vendor.user:
        messages.error(request, 'Você não tem permissão para visualizar este item.')
        return redirect('food_list')
    
    context = {
        'food_item': food_item,
    }
    return render(request, 'menu/food_detail.html', context)

@login_required(login_url='social_login')
def food_update(request, pk):
    """
    Atualiza uma refeição/lanche existente
    """
    food_item = get_object_or_404(FoodItem, pk=pk)
    
    # Verificar permissão (admin ou dono do restaurante)
    if not request.user.is_superuser and request.user != food_item.vendor.user:
        messages.error(request, 'Você não tem permissão para editar este item.')
        return redirect('food_list')
    
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES, instance=food_item)
        if form.is_valid():
            food_item = form.save(commit=False)
            food_item.slug = slugify(food_item.food_title)
            food_item.save()
            
            messages.success(request, f'Item {food_item.food_title} atualizado com sucesso!')
            return redirect('food_detail', pk=food_item.pk)
    else:
        form = FoodItemForm(instance=food_item)
        
        # Filtrar categorias do restaurante do usuário
        if not request.user.is_superuser:
            vendor = get_object_or_404(Vendor, user=request.user)
            form.fields['category'].queryset = Category.objects.filter(vendor=vendor)
    
    context = {
        'form': form,
        'food_item': food_item,
        'title': 'Editar Item do Cardápio',
    }
    return render(request, 'menu/food_form.html', context)

@login_required(login_url='social_login')
def food_delete(request, pk):
    """
    Exclui uma refeição/lanche
    """
    food_item = get_object_or_404(FoodItem, pk=pk)
    
    # Verificar permissão (admin ou dono do restaurante)
    if not request.user.is_superuser and request.user != food_item.vendor.user:
        messages.error(request, 'Você não tem permissão para excluir este item.')
        return redirect('food_list')
    
    if request.method == 'POST':
        food_title = food_item.food_title
        food_item.delete()
        messages.success(request, f'Item {food_title} excluído com sucesso!')
        return redirect('food_list')
    
    context = {
        'food_item': food_item,
    }
    return render(request, 'menu/food_delete.html', context)
