from django.shortcuts import render, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from accounts.views import check_role_vendor
from accounts.forms import UserProfileForm
from accounts.models import UserProfile
from menu.forms import CategoryForm, FoodItemForm
from menu.models import Category, FoodItem
from .forms import VendorForm
from .models import Vendor


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vprofile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    
    # Verificar se o usuário é restaurante, ou se precisa ser criado
    if hasattr(request.user, 'vendor'):  # Verifica se o usuário já tem um restaurante
        vendor = request.user.vendor
    else:
        vendor = None

    if request.method == 'POST':
        # Formulários de perfil e restaurante
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        vendor_form = VendorForm(request.POST, request.FILES, instance=vendor) if vendor else VendorForm(request.POST, request.FILES)

        if profile_form.is_valid() and vendor_form.is_valid():
            profile_form.save()

            if vendor:  # Se o restaurante já existe, apenas atualiza
                vendor_form.save()
            else:  # Se o restaurante não existe, cria um novo
                new_vendor = vendor_form.save(commit=False)
                
                # Garantir que o restaurante esteja associado ao usuário
                new_vendor.user = request.user
                new_vendor.user_profile = profile  # Associando o UserProfile ao Vendor
                
                # Geração única do vendor_slug, caso não tenha sido atribuído
                if not new_vendor.vendor_slug:
                    new_vendor.vendor_slug = slugify(new_vendor.vendor_name)
                
                # Verifica se o usuário já possui um Vendor
                if Vendor.objects.filter(user=request.user).exists():
                    messages.error(request, 'Este usuário já possui um restaurante registrado.')
                    return redirect('vprofile')

                new_vendor.save()

            messages.success(request, 'Alterações salvas com sucesso!')
            return redirect('vprofile')
        else:
            print(profile_form.errors)
            print(vendor_form.errors)
    else:
        # Carregar os formulários com os dados existentes
        profile_form = UserProfileForm(instance=profile)
        vendor_form = VendorForm(instance=vendor) if vendor else VendorForm()

    context = {
        'profile_form': profile_form,
        'vendor_form': vendor_form,
        'profile': profile,
        'vendor': vendor,
    }
    return render(request, 'vendor/vprofile.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def menu_builder(request):
    vendor = get_vendor(request.user)
    if not vendor:
        messages.error(request, 'Você não tem um restaurante associado à sua conta. Por favor, complete seu perfil.')
        return redirect('vprofile')

    # Caso o Vendor exista, recupera as categorias do restaurante
    categories = Category.objects.filter(vendor=vendor).order_by('create_at')

    context = {
        'categories': categories,
    }
    return render(request, 'vendor/menu_builder.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def fooditems_by_category(request, pk=None):
    vendor = get_vendor(request.user)
    category = get_object_or_404(Category, pk=pk, vendor=vendor)
    fooditems = FoodItem.objects.filter(vendor=vendor, category=category)
    context = {
        'fooditems': fooditems,
        'category': category,
    }
    return render(request, 'vendor/fooditems_by_category.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.vendor = Vendor.objects.get(user=request.user)
            category.slug = generate_unique_slug(Category, 'category_name', category.category_name)
            category.save()
            messages.success(request, 'Categoria adicionada com sucesso!')
            return redirect('menu_builder')
        else:
            messages.error(request, 'Houve um erro ao salvar a categoria. Por favor, tente novamente.')
            print(form.errors)
    else:
        form = CategoryForm()

    context = {
        'form': form,
    }
    return render(request, 'vendor/add_category.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def edit_category(request, pk=None):
    category = get_object_or_404(Category, pk=pk, vendor__user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save(commit=False)
            category.vendor = Vendor.objects.get(user=request.user)
            category.slug = generate_unique_slug(Category, 'category_name', category.category_name)
            category.save()
            messages.success(request, 'Categoria atualizada com sucesso!')
            return redirect('menu_builder')
        else:
            messages.error(request, 'Houve um erro ao salvar a categoria. Por favor, tente novamente.')
            print(form.errors)
    else:
        form = CategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
    }
    return render(request, 'vendor/edit_category.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def delete_category(request, pk=None):
    category = get_object_or_404(Category, pk=pk, vendor__user=request.user)
    category.delete()
    messages.success(request, 'Categoria excluída com sucesso!')
    return redirect('menu_builder')


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def add_food(request):
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES)
        if form.is_valid():
            food = form.save(commit=False)
            food.vendor = Vendor.objects.get(user=request.user)
            food.slug = generate_unique_slug(FoodItem, 'food_title', food.food_title)
            food.save()
            messages.success(request, 'Prato adicionado com sucesso!')
            return redirect('fooditems_by_category', food.category.id)
        else:
            messages.error(request, 'Houve um erro ao adicionar o prato. Por favor, tente novamente.')
            print(form.errors)
    else:
        form = FoodItemForm()

    context = {
        'form': form,
    }
    return render(request, 'vendor/add_food.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def delete_food(request, pk=None):
    food = get_object_or_404(FoodItem, pk=pk, vendor__user=request.user)
    category_id = food.category.id
    food.delete()
    messages.success(request, 'Prato excluído com sucesso!')
    return redirect('fooditems_by_category', category_id)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def edit_food(request, pk=None):
    vendor = get_object_or_404(Vendor, user=request.user)
    food = get_object_or_404(FoodItem, pk=pk, vendor=vendor)

    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES, instance=food)
        if form.is_valid():
            food_title = form.cleaned_data['food_title']
            food = form.save(commit=False)
            food.slug = generate_unique_slug(FoodItem, 'food_title', food_title)
            food.vendor = vendor
            food.save()
            messages.success(request, 'Prato atualizado com sucesso!')
            return redirect('fooditems_by_category', pk=food.category.id)
        else:
            messages.error(request, 'Houve um erro ao atualizar o prato. Por favor, tente novamente.')
            print(form.errors)
    else:
        form = FoodItemForm(instance=food)

    context = {
        'form': form,
        'food': food,
    }
    return render(request, 'vendor/edit_food.html', context)


# Função utilitária para gerar slugs únicos
def generate_unique_slug(model, field_name, field_value):
    slug = slugify(field_value)
    if model.objects.filter(slug=slug).exists():
        slug = f"{slug}-{model.objects.count() + 1}"
    return slug


# Função para obter o Vendor associado ao usuário
def get_vendor(user):
    try:
        return Vendor.objects.get(user=user)
    except Vendor.DoesNotExist:
        return None
