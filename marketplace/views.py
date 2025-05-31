"""
Arquivo: marketplace/views.py
Descrição: Contém as views principais do marketplace, incluindo:
- Página inicial do marketplace
- Gerenciamento de carrinho de compras
- Visualização de detalhes de restaurantes
- Busca geral de produtos e restaurantes
- Funcionalidades de favoritos
- Busca avançada de restaurantes e produtos

Dependências principais:
- vendor/models.py: Modelo Vendor
- menu/models.py: Modelos Category e FoodItem
- marketplace/models.py: Modelos Cart, FavoriteRestaurant, Tax, Order, OrderItem, Payment, Invoice
- accounts/models.py: Modelos UserProfile e UserAddress
"""

# Imports da biblioteca padrão Python
import os
import uuid
import json
import datetime

# Imports do Django
from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch, Avg, Count, Min, Max, Sum, F, DecimalField
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from django.template.loader import get_template
from django.contrib import messages

# Imports de bibliotecas de terceiros
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Imports locais (do próprio projeto )
from accounts.models import UserProfile, UserAddress
from menu.models import Category, FoodItem
from vendor.models import Vendor
from .models import Cart, FavoriteRestaurant, Tax, Order, OrderItem, Payment, Invoice


def marketplace(request):
    """
    Página inicial do marketplace.
    
    Exibe todos os restaurantes cadastrados, independente do status de aprovação.
    Em ambiente de produção, deve-se filtrar apenas restaurantes aprovados e ativos.
    
    Args:
        request: Objeto request do Django
        
    Returns:
        HttpResponse: Renderiza a página inicial do marketplace
    """
    # Removido filtro de aprovação e status do usuário para exibir todos os restaurantes cadastrados
    vendors = Vendor.objects.all()
    vendor_count = vendors.count()
    context = {
        'vendors': vendors,
        'vendor_count': vendor_count,
    }
    return render(request, 'marketplace/listings.html', context)


def vendor_detail(request, vendor_slug):
    """
    Exibe detalhes de um restaurante específico.
    
    Args:
        request: Objeto request do Django
        vendor_slug: Slug do restaurante a ser visualizado
        
    Returns:
        HttpResponse: Renderiza a página de detalhes do restaurante
    """
    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)
    
    # Verificar se o restaurante é favorito do usuário
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = FavoriteRestaurant.objects.filter(user=request.user, vendor=vendor).exists()
    
    # Obter categorias e itens do cardápio
    categories = Category.objects.filter(vendor=vendor)
    
    # Organizar itens por categoria
    menu_items = {}
    for category in categories:
        food_items = FoodItem.objects.filter(vendor=vendor, category=category, is_available=True)
        menu_items[category] = food_items
    
    context = {
        'vendor': vendor,
        'categories': categories,
        'menu_items': menu_items,
        'is_favorite': is_favorite,
    }
    
    return render(request, 'marketplace/vendor_detail.html', context)


def add_to_cart(request, food_id):
    """
    Adiciona um item ao carrinho de compras.
    
    Incrementa a quantidade se o item já estiver no carrinho.
    
    Args:
        request: Objeto request do Django
        food_id: ID do item de comida a ser adicionado
        
    Returns:
        JsonResponse: Resposta JSON com status da operação
    """
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    # Increase the cart quantity
                    chkCart.quantity += 1
                    chkCart.save()
                    return JsonResponse({'status': 'Success', 'message': 'Increased the cart quantity', 'qty': chkCart.quantity})
                except:
                    chkCart = Cart.objects.create(user=request.user, fooditem=fooditem, quantity=1)
                    return JsonResponse({'status': 'Success', 'message': 'Added the food to the cart', 'qty': chkCart.quantity})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This food does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
        
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})


def decrease_cart(request, food_id):
    """
    Diminui a quantidade de um item no carrinho.
    
    Remove o item se a quantidade chegar a zero.
    
    Args:
        request: Objeto request do Django
        food_id: ID do item de comida a ser diminuído
        
    Returns:
        JsonResponse: Resposta JSON com status da operação
    """
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    if chkCart.quantity > 1:
                        # decrease the cart quantity
                        chkCart.quantity -= 1
                        chkCart.save()
                    else:
                        chkCart.delete()
                        chkCart.quantity = 0
                    return JsonResponse({'status': 'Success', 'qty': chkCart.quantity})
                except:
                    return JsonResponse({'status': 'Failed', 'message': 'You do not have this item in your cart!'})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This food does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
        
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})


@login_required(login_url = 'login')
def cart(request):
    """
    Exibe o carrinho de compras do usuário.
    
    Mostra os itens no carrinho do usuário logado.
    
    Args:
        request: Objeto request do Django
        
    Returns:
        HttpResponse: Renderiza a página do carrinho de compras
    """
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    context = {
        'cart_items': cart_items,
    }
    return render(request, 'marketplace/cart.html', context)


def delete_cart(request, cart_id):
    """
    Remove um item do carrinho.
    
    Args:
        request: Objeto request do Django
        cart_id: ID do item no carrinho a ser removido
        
    Returns:
        JsonResponse: Resposta JSON com status da operação
    """
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                # Check if the cart item exists
                cart_item = Cart.objects.get(user=request.user, id=cart_id)
                if cart_item:
                    cart_item.delete()
                    return JsonResponse({'status': 'Success', 'message': 'Cart item has been deleted!'})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'Cart Item does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})


def search(request):
    """
    Busca geral de restaurantes por localização e palavra-chave.
    
    Permite buscar restaurantes por endereço, coordenadas e palavra-chave.
    
    Args:
        request: Objeto request do Django
        
    Returns:
        HttpResponse: Renderiza a página de resultados da busca
    """
    if not 'address' in request.GET:
        return redirect('marketplace')
    else:
        address = request.GET['address']
        latitude = request.GET['lat']
        longitude = request.GET['lng']
        radius = request.GET['radius']
        keyword = request.GET['keyword']

        # get vendor ids that has the food item the user is looking for
        fetch_vendors_by_fooditems = FoodItem.objects.filter(food_title__icontains=keyword, is_available=True).values_list('vendor', flat=True)
        
        vendors = Vendor.objects.filter(Q(id__in=fetch_vendors_by_fooditems) | Q(vendor_name__icontains=keyword, is_approved=True, user__is_active=True))

        vendor_count = vendors.count()
        context = {
            'vendors': vendors,
            'vendor_count': vendor_count,
            'source_location': address,
        }

        return render(request, 'marketplace/listings.html', context)


# --- Funcionalidades de busca e favoritos de restaurantes ---

def restaurant_search(request):
    """
    Página de busca pública de restaurantes com filtros avançados.
    
    Permite buscar restaurantes por palavra-chave, categoria, localização e favoritos,
    com opções de ordenação por relevância, avaliação ou proximidade.
    
    Args:
        request: Objeto request do Django
        
    Returns:
        HttpResponse: Renderiza a página de busca de restaurantes com resultados filtrados
    """
    # Parâmetros de busca e filtros
    keyword = request.GET.get('keyword', '')
    category_id = request.GET.get('category', '')
    address_id = request.GET.get('address', '')
    sort_by = request.GET.get('sort_by', 'relevance')  # relevance, rating, distance
    favorites_only = request.GET.get('favorites_only') == 'on'
    
    # Busca básica - restaurantes aprovados e ativos
    restaurants = Vendor.objects.filter(is_approved=True, user__is_active=True)
    
    # Filtro por favoritos (apenas para usuários logados)
    if favorites_only and request.user.is_authenticated:
        favorite_vendor_ids = FavoriteRestaurant.objects.filter(
            user=request.user
        ).values_list('vendor_id', flat=True)
        restaurants = restaurants.filter(id__in=favorite_vendor_ids)
    
    # Filtro por palavra-chave (nome do restaurante)
    if keyword:
        # Busca por nome do restaurante
        keyword_filter = Q(vendor_name__icontains=keyword) | Q(user__first_name__icontains=keyword)
        
        # Busca por itens do cardápio
        food_items = FoodItem.objects.filter(food_title__icontains=keyword, is_available=True)
        vendor_ids_with_matching_food = food_items.values_list('vendor', flat=True).distinct()
        
        # Combina os resultados
        keyword_filter |= Q(id__in=vendor_ids_with_matching_food)
        restaurants = restaurants.filter(keyword_filter)
    
    # Filtro por categoria de comida
    if category_id:
        try:
            category = Category.objects.get(id=category_id)
            # Encontra restaurantes que têm itens nesta categoria
            vendor_ids_with_category = FoodItem.objects.filter(
                category=category, 
                is_available=True
            ).values_list('vendor', flat=True).distinct()
            
            restaurants = restaurants.filter(id__in=vendor_ids_with_category)
        except Category.DoesNotExist:
            pass
    
    # Filtro por localização/proximidade
    user_location = None
    if address_id and request.user.is_authenticated:
        try:
            user_address = UserAddress.objects.get(id=address_id, user=request.user)
            user_location = {
                'latitude': user_address.latitude,
                'longitude': user_address.longitude
            }
            # Nota: Para implementar filtro por distância real, seria necessário
            # um campo de localização geográfica no modelo Vendor e usar
            # funções geoespaciais do banco de dados
        except UserAddress.DoesNotExist:
            pass
    
    # Ordenação dos resultados
    if sort_by == 'rating':
        # Exemplo: ordenar por avaliação média (se existir)
        # restaurants = restaurants.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
        restaurants = restaurants.order_by('-created_at')  # Fallback se não houver avaliações
    elif sort_by == 'distance' and user_location:
        # Ordenação por distância requer implementação geoespacial
        # Por enquanto, mantém a ordenação padrão
        restaurants = restaurants.order_by('-created_at')
    else:  # relevance (default)
        restaurants = restaurants.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(restaurants, 8)  # 8 restaurantes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obter todas as categorias para o filtro
    categories = Category.objects.all().distinct()
    
    # Obter endereços do usuário para o filtro de proximidade
    user_addresses = []
    if request.user.is_authenticated:
        user_addresses = UserAddress.objects.filter(user=request.user)
    
    # Verificar quais restaurantes são favoritos do usuário
    favorite_vendor_ids = []
    if request.user.is_authenticated:
        favorite_vendor_ids = FavoriteRestaurant.objects.filter(
            user=request.user
        ).values_list('vendor_id', flat=True)
    
    context = {
        'restaurants': page_obj,
        'restaurant_count': restaurants.count(),
        'keyword': keyword,
        'selected_category': category_id,
        'categories': categories,
        'selected_address': address_id,
        'user_addresses': user_addresses,
        'sort_by': sort_by,
        'favorites_only': favorites_only,
        'favorite_vendor_ids': favorite_vendor_ids,
    }
    
    return render(request, 'marketplace/restaurant_search.html', context)


def restaurant_detail(request, vendor_id):
    """
    Exibe detalhes de um restaurante específico com seu cardápio.
    
    Mostra informações detalhadas sobre um restaurante, incluindo categorias
    e itens do cardápio organizados por categoria.
    
    Args:
        request: Objeto request do Django
        vendor_id: ID do restaurante a ser visualizado
        
    Returns:
        HttpResponse: Renderiza a página de detalhes do restaurante
    """
    vendor = get_object_or_404(Vendor, pk=vendor_id, is_approved=True, user__is_active=True)
    
    # Verificar se o restaurante é favorito do usuário
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = FavoriteRestaurant.objects.filter(user=request.user, vendor=vendor).exists()
    
    # Obter categorias e itens do cardápio
    categories = Category.objects.filter(vendor=vendor)
    
    # Organizar itens por categoria
    menu_items = {}
    for category in categories:
        food_items = FoodItem.objects.filter(vendor=vendor, category=category, is_available=True)
        menu_items[category] = food_items
    
    context = {
        'vendor': vendor,
        'categories': categories,
        'menu_items': menu_items,
        'is_favorite': is_favorite,
    }
    
    return render(request, 'marketplace/restaurant_detail.html', context)


@login_required
def add_to_favorites(request, vendor_id):
    """
    Adiciona ou remove um restaurante dos favoritos do usuário.
    
    Funciona como um toggle: se o restaurante já é favorito, remove;
    se não é favorito, adiciona.
    
    Args:
        request: Objeto request do Django
        vendor_id: ID do restaurante a ser adicionado/removido dos favoritos
        
    Returns:
        JsonResponse: Resposta JSON com status da operação
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            vendor = Vendor.objects.get(id=vendor_id, is_approved=True)
            
            # Verificar se já é favorito
            favorite, created = FavoriteRestaurant.objects.get_or_create(
                user=request.user,
                vendor=vendor
            )
            
            # Se não foi criado, significa que já existia, então removemos
            if not created:
                favorite.delete()
                return JsonResponse({
                    'status': 'success', 
                    'action': 'removed',
                    'message': 'Restaurante removido dos favoritos'
                })
            
            return JsonResponse({
                'status': 'success', 
                'action': 'added',
                'message': 'Restaurante adicionado aos favoritos'
            })
        except Vendor.DoesNotExist:
            return JsonResponse({
                'status': 'failed', 
                'message': 'Restaurante não encontrado'
            })
    
    return JsonResponse({'status': 'failed', 'message': 'Requisição inválida'})


@login_required
def list_favorites(request):
    """
    Lista todos os restaurantes favoritos do usuário.
    
    Exibe uma página com todos os restaurantes que o usuário marcou como favorito.
    
    Args:
        request: Objeto request do Django
        
    Returns:
        HttpResponse: Renderiza a página de restaurantes favoritos
    """
    favorites = FavoriteRestaurant.objects.filter(user=request.user).select_related('vendor')
    
    context = {
        'favorites': favorites,
    }
    
    return render(request, 'marketplace/favorite_restaurants.html', context)


# --- Funcionalidades de busca de produtos com filtros ---

def product_search(request):
    """
    Página de busca pública de produtos com filtros avançados.
    
    Permite buscar produtos por palavra-chave, categoria, restaurante e faixa de preço,
    com opções de ordenação por relevância, preço ou popularidade.
    
    Args:
        request: Objeto request do Django
        
    Returns:
        HttpResponse: Renderiza a página de busca de produtos com resultados filtrados
    """
    # Parâmetros de busca e filtros
    keyword = request.GET.get('keyword', '')
    category_id = request.GET.get('category', '')
    vendor_id = request.GET.get('vendor', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    sort_by = request.GET.get('sort_by', 'relevance')  # relevance, price_asc, price_desc, popularity
    
    # Busca básica - produtos disponíveis
    products = FoodItem.objects.filter(is_available=True)
    
    # Filtro por palavra-chave (nome ou descrição do produto)
    if keyword:
        products = products.filter(
            Q(food_title__icontains=keyword) | 
            Q(description__icontains=keyword)
        )
    
    # Filtro por categoria
    if category_id:
        try:
            category = Category.objects.get(id=category_id)
            products = products.filter(category=category)
        except Category.DoesNotExist:
            pass
    
    # Filtro por restaurante
    if vendor_id:
        try:
            vendor = Vendor.objects.get(id=vendor_id, is_approved=True, user__is_active=True)
            products = products.filter(vendor=vendor)
        except Vendor.DoesNotExist:
            pass
    
    # Filtro por faixa de preço
    if price_min:
        try:
            price_min = float(price_min)
            products = products.filter(price__gte=price_min)
        except ValueError:
            pass
    
    if price_max:
        try:
            price_max = float(price_max)
            products = products.filter(price__lte=price_max)
        except ValueError:
            pass
    
    # Ordenação dos resultados
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'popularity':
        # Ordenar por popularidade (quantidade de vezes no carrinho)
        # Isso é um exemplo, pode ser adaptado conforme necessário
        products = products.annotate(cart_count=Count('cart')).order_by('-cart_count')
    else:  # relevance (default)
        # Para relevância, mantemos a ordem padrão ou podemos personalizar
        products = products.order_by('-updated_at')
    
    # Paginação
    paginator = Paginator(products, 12)  # 12 produtos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obter todas as categorias para o filtro
    categories = Category.objects.all().distinct()
    
    # Obter restaurantes aprovados para o filtro
    vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
    
    # Obter faixa de preços para os filtros
    price_range = FoodItem.objects.filter(is_available=True).aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Verificar itens no carrinho do usuário
    cart_items = []
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user).values_list('fooditem', flat=True)
    
    context = {
        'products': page_obj,
        'product_count': products.count(),
        'keyword': keyword,
        'selected_category': category_id,
        'categories': categories,
        'selected_vendor': vendor_id,
        'vendors': vendors,
        'price_min': price_min,
        'price_max': price_max,
        'price_range': price_range,
        'sort_by': sort_by,
        'cart_items': cart_items,
    }
    
    return render(request, 'marketplace/product_search.html', context)


def product_detail(request, product_id):
    """
    Exibe detalhes de um produto específico.
    
    Mostra informações detalhadas sobre um produto, incluindo descrição, preço,
    restaurante e produtos relacionados.
    
    Args:
        request: Objeto request do Django
        product_id: ID do produto a ser visualizado
        
    Returns:
        HttpResponse: Renderiza a página de detalhes do produto
    """
    product = get_object_or_404(FoodItem, pk=product_id, is_available=True)
    vendor = product.vendor
    
    # Verificar se o produto está no carrinho do usuário
    in_cart = False
    if request.user.is_authenticated:
        in_cart = Cart.objects.filter(user=request.user, fooditem=product).exists()
    
    # Produtos relacionados (mesma categoria)
    related_products = FoodItem.objects.filter(
        category=product.category, 
        is_available=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'vendor': vendor,
        'in_cart': in_cart,
        'related_products': related_products,
    }
    
    return render(request, 'marketplace/product_detail.html', context)


# --- Funcionalidades de checkout e pedidos ---

@login_required(login_url='login')
def checkout(request):
    """
    Página de checkout para finalizar o pedido.
    
    Permite ao usuário selecionar endereço de entrega, método de pagamento,
    adicionar observações e visualizar o resumo do pedido antes de finalizar.
    
    Args:
        request: Objeto request do Django
        
    Returns:
        HttpResponse: Renderiza a página de checkout ou redireciona para outra página
    """
    # Verificar se há itens no carrinho
    cart_items = Cart.objects.filter(user=request.user)
    if cart_items.count() <= 0:
        messages.warning(request, 'Seu carrinho está vazio. Adicione itens antes de prosseguir.')
        return redirect('marketplace')
    
    # Calcular valores do pedido
    subtotal = 0
    for item in cart_items:
        subtotal += item.fooditem.price * item.quantity
    
    # Obter taxas ativas
    tax_dict = {}
    taxes = Tax.objects.filter(is_active=True)
    for tax in taxes:
        tax_amount = (tax.tax_percentage * subtotal) / 100
        tax_dict[tax.tax_type] = {str(tax.tax_percentage): tax_amount}
    
    # Calcular total com taxas
    tax_total = sum(sum(value.values()) for value in tax_dict.values())
    grand_total = subtotal + tax_total
    
    # Obter endereços do usuário
    addresses = UserAddress.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()
    
    if request.method == 'POST':
        # Processar formulário de checkout
        address_id = request.POST.get('address')
        payment_method = request.POST.get('payment_method')
        order_note = request.POST.get('order_note', '')
        
        if not address_id:
            messages.error(request, 'Por favor, selecione um endereço de entrega.')
            return redirect('checkout')
        
        # Obter endereço selecionado
        address = get_object_or_404(UserAddress, id=address_id, user=request.user)
        
        # Criar pedido
        order = Order(
            user=request.user,
            address=address,
            order_total=grand_total,
            tax=tax_total,
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            phone=request.user.phone_number if hasattr(request.user, 'phone_number') else '',
            email=request.user.email,
            address_line_1=address.address_line1,
            address_line_2=address.address_line2 if hasattr(address, 'address_line2') else '',
            city=address.city,
            state=address.state,
            country=address.country,
            postal_code=address.postal_code,
            order_note=order_note
        )
        order.save()
        
        # Gerar número do pedido
        order.order_number = order.generate_order_number()
        order.save()
        
        # Adicionar vendors ao pedido
        vendors = set()
        for item in cart_items:
            vendors.add(item.fooditem.vendor)
        for vendor in vendors:
            order.vendors.add(vendor)
        
        # Criar itens do pedido
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                fooditem=item.fooditem,
                quantity=item.quantity,
                price=item.fooditem.price,
                amount=item.fooditem.price * item.quantity
            )
        
        # Processar pagamento
        if payment_method == 'CREDIT_CARD' or payment_method == 'DEBIT_CARD':
            # Simulação de pagamento com cartão
            return redirect('payment', order_id=order.id, payment_method=payment_method)
        elif payment_method == 'PIX':
            # Simulação de pagamento com PIX
            return redirect('payment', order_id=order.id, payment_method=payment_method)
        else:  # CASH
            # Pagamento na entrega
            payment = Payment(
                user=request.user,
                order=order,
                payment_id=f'CASH_{uuid.uuid4().hex[:10].upper()}',
                payment_method='CASH',
                amount_paid=grand_total,
                status='PENDING'
            )
            payment.save()
            
            # Atualizar status do pedido
            order.payment_status = 'PENDING'
            order.is_ordered = True
            order.save()
            
            # Limpar carrinho
            cart_items.delete()
            
            # Redirecionar para página de confirmação
            return redirect('order_complete', order_number=order.order_number)
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax_dict': tax_dict,
        'grand_total': grand_total,
        'addresses': addresses,
        'default_address': default_address,
    }
    
    return render(request, 'marketplace/checkout.html', context)


@login_required(login_url='login')
def payment(request, order_id, payment_method):
    """
    Página de pagamento para processar o pagamento do pedido.
    
    Permite ao usuário realizar o pagamento do pedido usando o método selecionado.
    
    Args:
        request: Objeto request do Django
        order_id: ID do pedido a ser pago
        payment_method: Método de pagamento selecionado
        
    Returns:
        HttpResponse: Renderiza a página de pagamento ou redireciona para confirmação
    """
    # Obter pedido
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        # Processar pagamento
        # Simulação de processamento de pagamento
        payment_status = 'PAID'  # Simulação de pagamento bem-sucedido
        
        # Criar registro de pagamento
        payment = Payment(
            user=request.user,
            order=order,
            payment_id=f'{payment_method}_{uuid.uuid4().hex[:10].upper()}',
            payment_method=payment_method,
            amount_paid=order.order_total,
            status=payment_status
        )
        payment.save()
        
        # Atualizar status do pedido
        order.payment_status = payment_status
        order.is_ordered = True
        order.status = 'CONFIRMED'
        order.save()
        
        # Limpar carrinho
        Cart.objects.filter(user=request.user).delete()
        
        # Redirecionar para página de confirmação
        return redirect('order_complete', order_number=order.order_number)
    
    context = {
        'order': order,
        'payment_method': payment_method,
    }
    
    if payment_method == 'CREDIT_CARD' or payment_method == 'DEBIT_CARD':
        return render(request, 'marketplace/payment_card.html', context)
    elif payment_method == 'PIX':
        return render(request, 'marketplace/payment_pix.html', context)
    else:
        return redirect('checkout')


@login_required(login_url='login')
def order_complete(request, order_number):
    """
    Página de confirmação do pedido.
    
    Exibe os detalhes do pedido finalizado, incluindo itens, valores e status.
    
    Args:
        request: Objeto request do Django
        order_number: Número do pedido finalizado
        
    Returns:
        HttpResponse: Renderiza a página de confirmação do pedido
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    ordered_food = OrderItem.objects.filter(order=order)
    
    subtotal = 0
    for item in ordered_food:
        subtotal += item.price * item.quantity
    
    tax_data = json.loads(order.tax)
    
    context = {
        'order': order,
        'ordered_food': ordered_food,
        'subtotal': subtotal,
        'tax_data': tax_data,
    }
    
    return render(request, 'marketplace/order_complete.html', context)


@login_required(login_url='login')
def my_orders(request):
    """
    Página de pedidos do usuário.
    
    Lista todos os pedidos realizados pelo usuário logado.
    
    Args:
        request: Objeto request do Django
        
    Returns:
        HttpResponse: Renderiza a página de pedidos do usuário
    """
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'marketplace/my_orders.html', context)


@login_required(login_url='login')
def order_detail(request, order_number):
    """
    Página de detalhes do pedido.
    
    Exibe informações detalhadas sobre um pedido específico.
    
    Args:
        request: Objeto request do Django
        order_number: Número do pedido a ser visualizado
        
    Returns:
        HttpResponse: Renderiza a página de detalhes do pedido
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    ordered_food = OrderItem.objects.filter(order=order)
    
    subtotal = 0
    for item in ordered_food:
        subtotal += item.price * item.quantity
    
    context = {
        'order': order,
        'ordered_food': ordered_food,
        'subtotal': subtotal,
    }
    
    return render(request, 'marketplace/order_detail.html', context)


# --- Funcionalidades de notas fiscais ---

@login_required(login_url='login')
def generate_invoice(request, order_number):
    """
    Gera a nota fiscal para um pedido específico.
    
    Cria um arquivo PDF com os detalhes do pedido e o disponibiliza para download.
    
    Args:
        request: Objeto request do Django
        order_number: Número do pedido para o qual gerar a nota fiscal
        
    Returns:
        FileResponse: Arquivo PDF da nota fiscal para download
    """
    # Obter o pedido
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Verificar se o pedido está pago
    if order.payment_status != 'PAID':
        messages.error(request, 'A nota fiscal só pode ser gerada para pedidos pagos.')
        return redirect('order_detail', order_number=order_number)
    
    # Verificar se já existe uma nota fiscal para este pedido
    try:
        invoice = Invoice.objects.get(order=order)
        # Se já existe, apenas retorna o PDF existente
        if invoice.pdf_file:
            return FileResponse(open(invoice.pdf_file.path, 'rb'), 
                               content_type='application/pdf',
                               as_attachment=True, 
                               filename=f'nota_fiscal_{invoice.invoice_number}.pdf')
    except Invoice.DoesNotExist:
        # Criar nova nota fiscal
        invoice = Invoice(order=order)
        invoice.save()
        
        # Gerar número da nota fiscal
        invoice.invoice_number = invoice.generate_invoice_number()
        invoice.save()
    
    # Obter itens do pedido
    ordered_food = OrderItem.objects.filter(order=order)
    
    # Calcular subtotal
    subtotal = 0
    for item in ordered_food:
        subtotal += item.price * item.quantity
    
    # Preparar contexto para o template
    context = {
        'order': order,
        'ordered_food': ordered_food,
        'subtotal': subtotal,
        'invoice': invoice,
        'invoice_date': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
        'company_name': 'iFood Clone',
        'company_address': 'Av. Exemplo, 123 - São Paulo/SP',
        'company_cnpj': '12.345.678/0001-90',
    }
    
    # Gerar HTML da nota fiscal
    template = get_template('marketplace/invoice_template.html')
    html_string = template.render(context)
    
    # Configurar fontes
    font_config = FontConfiguration()
    
    # Definir caminho para salvar o PDF
    invoice_directory = os.path.join(settings.MEDIA_ROOT, 'invoices')
    os.makedirs(invoice_directory, exist_ok=True)
    pdf_file_path = os.path.join(invoice_directory, f'invoice_{invoice.invoice_number}.pdf')
    
    # Gerar PDF
    HTML(string=html_string).write_pdf(
        pdf_file_path,
        font_config=font_config,
        stylesheets=[
            CSS(string='''
                @page {
                    size: letter;
                    margin: 1.5cm;
                }
                body {
                    font-family: "Noto Sans CJK SC", "WenQuanYi Zen Hei", sans-serif;
                }
            ''')
        ]
    )
    
    # Atualizar caminho do arquivo no modelo
    invoice.pdf_file = f'invoices/invoice_{invoice.invoice_number}.pdf'
    invoice.save()
    
    # Retornar o PDF gerado
    return FileResponse(
        open(pdf_file_path, 'rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=f'nota_fiscal_{invoice.invoice_number}.pdf'
    )


@login_required(login_url='login')
def view_invoice(request, order_number):
    """
    Visualiza a nota fiscal de um pedido específico.
    
    Exibe o PDF da nota fiscal no navegador sem fazer download.
    
    Args:
        request: Objeto request do Django
        order_number: Número do pedido cuja nota fiscal será visualizada
        
    Returns:
        FileResponse: Arquivo PDF da nota fiscal para visualização
    """
    # Obter o pedido
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Verificar se existe uma nota fiscal para este pedido
    try:
        invoice = Invoice.objects.get(order=order)
        if invoice.pdf_file:
            # Retornar o PDF para visualização (não como anexo)
            return FileResponse(
                open(invoice.pdf_file.path, 'rb'),
                content_type='application/pdf'
            )
        else:
            messages.error(request, 'O arquivo PDF da nota fiscal não foi encontrado.')
            return redirect('order_detail', order_number=order_number)
    except Invoice.DoesNotExist:
        messages.error(request, 'Não existe nota fiscal para este pedido.')
        return redirect('order_detail', order_number=order_number)


@login_required(login_url='login')
def invoice_list(request):
    """
    Lista todas as notas fiscais do usuário.
    
    Exibe uma página com todas as notas fiscais dos pedidos do usuário.
    
    Args:
        request: Objeto request do Django
        
    Returns:
        HttpResponse: Renderiza a página de listagem de notas fiscais
    """
    # Obter pedidos do usuário que possuem nota fiscal
    invoices = Invoice.objects.filter(order__user=request.user).order_by('-invoice_date')
    
    context = {
        'invoices': invoices,
    }
    
    return render(request, 'marketplace/invoice_list.html', context)
