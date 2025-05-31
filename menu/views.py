# menu/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.urls import reverse # Importar reverse

# Imports locais (do próprio projeto)
# Importando check_role_vendor e check_role_admin de accounts.utils
from accounts.utils import check_role_vendor, check_role_admin 
from vendor.models import Vendor
from .models import Category, FoodItem
from .forms import CategoryForm, FoodItemForm

# --- CRUD de Categorias ---

# CORRIGIDO: login_url e user_passes_test
@login_required(login_url='request_otp')
# @user_passes_test(check_role_vendor, login_url='request_otp') # Vendor ou Admin podem listar?
# Se admin também pode, remover user_passes_test ou criar um teste combinado
def category_list(request):
    """
    Lista todas as categorias do restaurante do usuário logado (se vendor)
    ou todas as categorias (se admin).
    """
    vendor = None
    if not request.user.is_superuser:
        try:
            vendor = Vendor.objects.get(user=request.user)
            categories = Category.objects.filter(vendor=vendor).order_by('category_name')
        except Vendor.DoesNotExist:
            messages.error(request, "Perfil de restaurante não encontrado.")
            return redirect(reverse('home')) # Ou para dashboard apropriado
    else:
        categories = Category.objects.all().order_by('vendor__vendor_name', 'category_name')

    context = {
        'categories': categories,
        'vendor': vendor, # Passa o vendor para o template, se aplicável
    }
    # Certifique-se que o template existe e está correto
    return render(request, 'menu/category_list.html', context) 

# CORRIGIDO: Nome da função, login_url, user_passes_test, redirect
@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def category_create(request): # Renomeado de add_category
    """
    Adiciona uma nova categoria ao restaurante do usuário logado
    """
    if not check_role_vendor(request.user):
        messages.error(request, "Acesso restrito.")
        return redirect(reverse('home'))
        
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        messages.error(request, "Perfil de restaurante não encontrado.")
        return redirect(reverse('home'))
        
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data['category_name']
            category = form.save(commit=False)
            category.vendor = vendor
            category.slug = slugify(category_name)
            category.save()
            messages.success(request, 'Categoria adicionada com sucesso!')
            # CORRIGIDO: Redireciona para a lista de categorias
            return redirect(reverse('category_list')) 
        else:
            messages.error(request, 'Erro ao adicionar categoria. Por favor, corrija os erros abaixo.')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
    }
    # Certifique-se que o template existe
    return render(request, 'menu/category_form.html', context) 

# CORRIGIDO: Nome da função, login_url, user_passes_test, redirect
@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def category_update(request, pk=None): # Renomeado de edit_category
    """
    Edita uma categoria existente do restaurante do usuário logado
    """
    category = get_object_or_404(Category, pk=pk)
    
    # Verificar permissão
    if not request.user.is_superuser and category.vendor.user != request.user:
        messages.error(request, 'Você não tem permissão para editar esta categoria.')
        return redirect(reverse('category_list'))
        
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category_name = form.cleaned_data['category_name']
            category = form.save(commit=False)
            category.slug = slugify(category_name)
            category.save()
            messages.success(request, 'Categoria atualizada com sucesso!')
            # CORRIGIDO: Redireciona para a lista de categorias
            return redirect(reverse('category_list')) 
        else:
            messages.error(request, 'Erro ao atualizar categoria. Por favor, corrija os erros abaixo.')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
    }
    # Certifique-se que o template existe
    return render(request, 'menu/category_form.html', context) 

# CORRIGIDO: Nome da função, login_url, user_passes_test, redirect
@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def category_delete(request, pk=None): # Renomeado de delete_category
    """
    Exclui uma categoria do restaurante do usuário logado
    """
    category = get_object_or_404(Category, pk=pk)
    
    # Verificar permissão
    if not request.user.is_superuser and category.vendor.user != request.user:
        messages.error(request, 'Você não tem permissão para excluir esta categoria.')
        return redirect(reverse('category_list'))

    # Idealmente, usar método POST para exclusão
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Categoria excluída com sucesso!')
        return redirect(reverse('category_list'))
    else:
        # Mostrar confirmação em GET (template não fornecido)
        # return render(request, 'menu/category_confirm_delete.html', {'category': category})
        # Por enquanto, apenas redireciona se não for POST
        messages.warning(request, 'Use o botão de confirmação para excluir.')
        return redirect(reverse('category_list'))


# --- CRUD de Itens de Comida ---

# CRIADO: Placeholder para food_list (listar todos os itens do vendor)
@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def food_list(request):
    """
    Lista todos os itens de comida do restaurante do usuário logado.
    Permite filtrar por nome, categoria e disponibilidade.
    """
    if not check_role_vendor(request.user):
        messages.error(request, "Acesso restrito.")
        return redirect(reverse('home'))
        
    try:
        vendor = Vendor.objects.get(user=request.user)
        
        # Obter todas as categorias do vendor para o filtro
        categories = Category.objects.filter(vendor=vendor).order_by('category_name')
        
        # Iniciar com todos os itens do vendor
        fooditems = FoodItem.objects.filter(vendor=vendor)
        
        # Aplicar filtros se fornecidos
        search_query = request.GET.get('search', '')
        category_filter = request.GET.get('category', '')
        availability_filter = request.GET.get('availability', '')
        
        # Filtrar por termo de busca
        if search_query:
            fooditems = fooditems.filter(
                Q(food_title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Filtrar por categoria
        if category_filter:
            fooditems = fooditems.filter(category__id=category_filter)
        
        # Filtrar por disponibilidade
        if availability_filter:
            is_available = availability_filter == 'available'
            fooditems = fooditems.filter(is_available=is_available)
        
        # Ordenar resultados
        fooditems = fooditems.order_by('category__category_name', 'food_title')
        
    except Vendor.DoesNotExist:
        messages.error(request, "Perfil de restaurante não encontrado.")
        return redirect(reverse('home'))

    context = {
        'food_items': fooditems,
        'categories': categories,
        'vendor': vendor,
        'search_query': search_query,
        'category_filter': category_filter,
        'availability_filter': availability_filter,
    }
    # Certifique-se que o template existe
    return render(request, 'menu/food_list.html', context)

# CORRIGIDO: Nome da função, login_url, user_passes_test, redirect
@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def food_create(request): # Renomeado de add_food
    """
    Adiciona um novo item de comida ao restaurante do usuário logado
    """
    if not check_role_vendor(request.user):
        messages.error(request, "Acesso restrito.")
        return redirect(reverse('home'))
        
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        messages.error(request, "Perfil de restaurante não encontrado.")
        return redirect(reverse('home'))
        
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES)
        # Filtrar queryset de categoria ANTES de validar
        form.fields['category'].queryset = Category.objects.filter(vendor=vendor)
        
        if form.is_valid():
            food_title = form.cleaned_data['food_title']
            food = form.save(commit=False)
            food.vendor = vendor
            food.slug = slugify(food_title)
            food.save()
            messages.success(request, 'Item de comida adicionado com sucesso!')
            # CORRIGIDO: Redireciona para a lista de itens
            return redirect(reverse('food_list')) 
        else:
            messages.error(request, 'Erro ao adicionar item de comida. Por favor, corrija os erros abaixo.')
    else:
        form = FoodItemForm()
        # Filtrar queryset de categoria para o formulário GET
        form.fields['category'].queryset = Category.objects.filter(vendor=vendor)
    
    context = {
        'form': form,
    }
    # Certifique-se que o template existe
    return render(request, 'menu/food_form.html', context) 

# CRIADO: Placeholder para food_detail
@login_required(login_url='request_otp')
# @user_passes_test(check_role_vendor, login_url='request_otp') # Ou permitir admin?
def food_detail(request, pk=None):
    """
    Exibe detalhes de um item de comida específico.
    """
    food = get_object_or_404(FoodItem, pk=pk)
    
    # Verificar permissão (vendor dono ou admin)
    if not request.user.is_superuser and food.vendor.user != request.user:
         messages.error(request, 'Você não tem permissão para ver este item.')
         return redirect(reverse('food_list')) # Ou para onde for apropriado
         
    context = {
        'food': food,
    }
    # Certifique-se que o template existe
    return render(request, 'menu/food_detail.html', context) 

# CORRIGIDO: Nome da função, login_url, user_passes_test, redirect
@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def food_update(request, pk=None): # Renomeado de edit_food
    """
    Edita um item de comida existente do restaurante do usuário logado
    """
    food = get_object_or_404(FoodItem, pk=pk)
    
    # Verificar permissão
    if not request.user.is_superuser and food.vendor.user != request.user:
        messages.error(request, 'Você não tem permissão para editar este item de comida.')
        return redirect(reverse('food_list'))
        
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
         # Se for admin editando, não precisa do vendor do request.user
         if not request.user.is_superuser:
            messages.error(request, "Perfil de restaurante não encontrado.")
            return redirect(reverse('home'))
         vendor = food.vendor # Admin edita item do vendor correto
         
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES, instance=food)
        # Filtrar queryset de categoria ANTES de validar
        form.fields['category'].queryset = Category.objects.filter(vendor=vendor)
        
        if form.is_valid():
            food_title = form.cleaned_data['food_title']
            food = form.save(commit=False)
            food.slug = slugify(food_title)
            food.save()
            messages.success(request, 'Item de comida atualizado com sucesso!')
            # CORRIGIDO: Redireciona para a lista de itens
            return redirect(reverse('food_list')) 
        else:
            messages.error(request, 'Erro ao atualizar item de comida. Por favor, corrija os erros abaixo.')
    else:
        form = FoodItemForm(instance=food)
        # Filtrar queryset de categoria para o formulário GET
        form.fields['category'].queryset = Category.objects.filter(vendor=vendor)
    
    context = {
        'form': form,
        'food': food,
    }
    # Certifique-se que o template existe
    return render(request, 'menu/food_form.html', context) 

# CORRIGIDO: Nome da função, login_url, user_passes_test, redirect
@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def food_delete(request, pk=None): # Renomeado de delete_food
    """
    Exclui um item de comida do restaurante do usuário logado
    """
    food = get_object_or_404(FoodItem, pk=pk)
    
    # Verificar permissão
    if not request.user.is_superuser and food.vendor.user != request.user:
        messages.error(request, 'Você não tem permissão para excluir este item de comida.')
        return redirect(reverse('food_list'))

    # Idealmente, usar método POST para exclusão
    if request.method == 'POST':
        food.delete()
        messages.success(request, 'Item de comida excluído com sucesso!')
        return redirect(reverse('food_list'))
    else:
        # Mostrar confirmação em GET (template não fornecido)
        # return render(request, 'menu/food_confirm_delete.html', {'food': food})
        # Por enquanto, apenas redireciona se não for POST
        messages.warning(request, 'Use o botão de confirmação para excluir.')
        return redirect(reverse('food_list'))

# REMOVIDO: fooditems_by_category (se food_list cobre a necessidade)
# Se precisar listar por categoria específica, pode recriar ou ajustar food_list com filtro

