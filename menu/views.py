"""
Arquivo: menu/views.py
Descrição: Contém todas as views relacionadas ao gerenciamento de cardápio, incluindo:
- CRUD de categorias de alimentos
- CRUD de itens de comida
- Visualização e organização do cardápio

Dependências principais:
- menu/models.py: Modelos de categoria e item de comida
- menu/forms.py: Formulários para manipulação de dados do cardápio
- vendor/models.py: Modelo de restaurante
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
        categories = Category.objects.all().order_by('category_name')
    else:
        vendor = get_object_or_404(Vendor, user=request.user)
        categories = Category.objects.filter(vendor=vendor).order_by('category_name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'vendor/menu_builder.html', context)


@login_required(login_url='social_login')
@user_passes_test(check_role_vendor)
def add_category(request):
    """
    Adiciona uma nova categoria ao restaurante do usuário logado
    """
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data['category_name']
            category = form.save(commit=False)
            category.vendor = Vendor.objects.get(user=request.user)
            
            # Gerar slug a partir do nome da categoria
            category.slug = slugify(category_name)
            category.save()
            
            messages.success(request, 'Categoria adicionada com sucesso!')
            return redirect('menu_builder')
        else:
            messages.error(request, 'Erro ao adicionar categoria. Por favor, corrija os erros abaixo.')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
    }
    return render(request, 'vendor/add_category.html', context)


@login_required(login_url='social_login')
@user_passes_test(check_role_vendor)
def edit_category(request, pk=None):
    """
    Edita uma categoria existente do restaurante do usuário logado
    """
    category = get_object_or_404(Category, pk=pk)
    
    # Verificar se a categoria pertence ao restaurante do usuário logado
    if request.user.is_superuser or category.vendor.user == request.user:
        if request.method == 'POST':
            form = CategoryForm(request.POST, instance=category)
            if form.is_valid():
                category_name = form.cleaned_data['category_name']
                category = form.save(commit=False)
                category.slug = slugify(category_name)
                category.save()
                
                messages.success(request, 'Categoria atualizada com sucesso!')
                return redirect('menu_builder')
            else:
                messages.error(request, 'Erro ao atualizar categoria. Por favor, corrija os erros abaixo.')
        else:
            form = CategoryForm(instance=category)
        
        context = {
            'form': form,
            'category': category,
        }
        return render(request, 'vendor/edit_category.html', context)
    else:
        messages.error(request, 'Você não tem permissão para editar esta categoria.')
        return redirect('menu_builder')


@login_required(login_url='social_login')
@user_passes_test(check_role_vendor)
def delete_category(request, pk=None):
    """
    Exclui uma categoria do restaurante do usuário logado
    """
    category = get_object_or_404(Category, pk=pk)
    
    # Verificar se a categoria pertence ao restaurante do usuário logado
    if request.user.is_superuser or category.vendor.user == request.user:
        category.delete()
        messages.success(request, 'Categoria excluída com sucesso!')
        return redirect('menu_builder')
    else:
        messages.error(request, 'Você não tem permissão para excluir esta categoria.')
        return redirect('menu_builder')


# --- CRUD de Itens de Comida ---

@login_required(login_url='social_login')
def fooditems_by_category(request, pk=None):
    """
    Lista todos os itens de comida de uma categoria específica
    """
    category = get_object_or_404(Category, pk=pk)
    
    if request.user.is_superuser:
        fooditems = FoodItem.objects.filter(category=category).order_by('food_title')
    else:
        vendor = get_object_or_404(Vendor, user=request.user)
        fooditems = FoodItem.objects.filter(vendor=vendor, category=category).order_by('food_title')
    
    context = {
        'fooditems': fooditems,
        'category': category,
    }
    return render(request, 'vendor/fooditems_by_category.html', context)


@login_required(login_url='social_login')
@user_passes_test(check_role_vendor)
def add_food(request):
    """
    Adiciona um novo item de comida ao restaurante do usuário logado
    """
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES)
        if form.is_valid():
            food_title = form.cleaned_data['food_title']
            food = form.save(commit=False)
            food.vendor = Vendor.objects.get(user=request.user)
            food.slug = slugify(food_title)
            food.save()
            
            messages.success(request, 'Item de comida adicionado com sucesso!')
            return redirect('fooditems_by_category', pk=food.category.id)
        else:
            messages.error(request, 'Erro ao adicionar item de comida. Por favor, corrija os erros abaixo.')
    else:
        # Filtrar categorias do restaurante do usuário logado
        vendor = get_object_or_404(Vendor, user=request.user)
        form = FoodItemForm(initial={'vendor': vendor})
        form.fields['category'].queryset = Category.objects.filter(vendor=vendor)
    
    context = {
        'form': form,
    }
    return render(request, 'vendor/add_food.html', context)


@login_required(login_url='social_login')
@user_passes_test(check_role_vendor)
def edit_food(request, pk=None):
    """
    Edita um item de comida existente do restaurante do usuário logado
    """
    food = get_object_or_404(FoodItem, pk=pk)
    
    # Verificar se o item de comida pertence ao restaurante do usuário logado
    if request.user.is_superuser or food.vendor.user == request.user:
        if request.method == 'POST':
            form = FoodItemForm(request.POST, request.FILES, instance=food)
            if form.is_valid():
                food_title = form.cleaned_data['food_title']
                food = form.save(commit=False)
                food.slug = slugify(food_title)
                food.save()
                
                messages.success(request, 'Item de comida atualizado com sucesso!')
                return redirect('fooditems_by_category', pk=food.category.id)
            else:
                messages.error(request, 'Erro ao atualizar item de comida. Por favor, corrija os erros abaixo.')
        else:
            # Filtrar categorias do restaurante do usuário logado
            vendor = get_object_or_404(Vendor, user=request.user)
            form = FoodItemForm(instance=food)
            form.fields['category'].queryset = Category.objects.filter(vendor=vendor)
        
        context = {
            'form': form,
            'food': food,
        }
        return render(request, 'vendor/edit_food.html', context)
    else:
        messages.error(request, 'Você não tem permissão para editar este item de comida.')
        return redirect('menu_builder')


@login_required(login_url='social_login')
@user_passes_test(check_role_vendor)
def delete_food(request, pk=None):
    """
    Exclui um item de comida do restaurante do usuário logado
    """
    food = get_object_or_404(FoodItem, pk=pk)
    
    # Verificar se o item de comida pertence ao restaurante do usuário logado
    if request.user.is_superuser or food.vendor.user == request.user:
        category_id = food.category.id
        food.delete()
        messages.success(request, 'Item de comida excluído com sucesso!')
        return redirect('fooditems_by_category', pk=category_id)
    else:
        messages.error(request, 'Você não tem permissão para excluir este item de comida.')
        return redirect('menu_builder')
