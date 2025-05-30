"""
Arquivo: accounts/views.py
Descrição: Contém as views relacionadas à autenticação e gerenciamento de contas,
incluindo login, registro, verificação OTP, dashboards e perfis de usuário.

Dependências principais:
- accounts/models.py: Modelos User e UserProfile
- accounts/forms.py: Formulários para autenticação e perfil
- vendor/models.py: Modelo Vendor para restaurantes
"""

# Imports da biblioteca padrão Python
import datetime
import random
import re
from datetime import date

# Imports do Django
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone

# Imports locais (do próprio projeto)
from accounts.forms import (AccountTypeForm, CustomerProfileForm, EmailForm,
                          OTPForm, RestaurantProfileForm, UserForm,
                          UserProfileForm)
from accounts.models import User, UserProfile
from accounts.utils import check_role_customer, check_role_vendor, send_otp_email
from marketplace.models import Order
from vendor.models import Vendor


def request_otp(request):
    """
    Exibe formulário para solicitar código OTP via email.
    
    Permite que usuários solicitem um código de verificação para
    autenticação ou recuperação de senha.
    """
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Verificar se o usuário existe
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                
                # Gerar e enviar OTP
                otp = ''.join(random.choices('0123456789', k=6))
                user.otp = otp
                user.otp_expiry = timezone.now() + datetime.timedelta(minutes=10)
                user.save()
                
                # Enviar email com OTP
                mail_subject = 'Código de Verificação para Login'
                email_template = 'accounts/emails/otp_email.html'
                send_otp_email(user, mail_subject, email_template)
                
                messages.success(request, 'Código de verificação enviado para seu email.')
                return redirect('verify_otp')
            else:
                # Criar novo usuário com OTP
                user = User.objects.create_user(email=email)
                user.set_unusable_password()
                
                # Gerar e enviar OTP
                otp = ''.join(random.choices('0123456789', k=6))
                user.otp = otp
                user.otp_expiry = timezone.now() + datetime.timedelta(minutes=10)
                user.save()
                
                # Enviar email com OTP
                mail_subject = 'Código de Verificação para Cadastro'
                email_template = 'accounts/emails/otp_email.html'
                send_otp_email(user, mail_subject, email_template)
                
                messages.success(request, 'Código de verificação enviado para seu email.')
                return redirect('verify_otp')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = EmailForm()
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/request_otp.html', context)


def verify_otp(request):
    """
    Verifica o código OTP fornecido pelo usuário.
    
    Se o código for válido, autentica o usuário e redireciona
    para a página apropriada com base no status da conta.
    """
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            
            # Verificar se existe usuário com este OTP e se não expirou
            users = User.objects.filter(otp=otp, otp_expiry__gt=timezone.now())
            if users.exists():
                user = users.first()
                
                # Limpar OTP após uso
                user.otp = None
                user.otp_expiry = None
                user.save()
                
                # Autenticar usuário
                auth.login(request, user)
                
                # Verificar se é primeiro login
                if not user.first_name and not user.last_name:
                    messages.info(request, 'Por favor, escolha o tipo de conta.')
                    return redirect('choose_account_type')
                
                # Verificar se tem perfil completo
                try:
                    profile = UserProfile.objects.get(user=user)
                    if not profile.address_line_1:
                        messages.info(request, 'Por favor, complete seu perfil.')
                        return redirect('complete_profile')
                except UserProfile.DoesNotExist:
                    messages.info(request, 'Por favor, complete seu perfil.')
                    return redirect('complete_profile')
                
                # Redirecionar com base no tipo de usuário
                return redirect('myAccount')
            else:
                messages.error(request, 'Código inválido ou expirado.')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = OTPForm()
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/verify_otp.html', context)


def registerUser(request):
    """
    Registra um novo usuário cliente.
    
    Obsoleto: Mantido para compatibilidade, mas o fluxo
    principal agora usa OTP.
    """
    return redirect('request_otp')


def registerVendor(request):
    """
    Registra um novo usuário restaurante.
    
    Obsoleto: Mantido para compatibilidade, mas o fluxo
    principal agora usa OTP.
    """
    return redirect('request_otp')


def login(request):
    """
    Autentica um usuário existente.
    
    Obsoleto: Mantido para compatibilidade, mas o fluxo
    principal agora usa OTP.
    """
    return redirect('request_otp')


def logout(request):
    """
    Encerra a sessão do usuário atual.
    """
    auth.logout(request)
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('request_otp')


def choose_account_type(request):
    """
    Permite ao usuário escolher entre conta de cliente ou restaurante.
    
    Exibe um formulário para seleção do tipo de conta após o
    primeiro login com OTP.
    """
    if request.user.first_name:
        messages.warning(request, 'Você já escolheu o tipo de conta.')
        return redirect('myAccount')
        
    if request.method == 'POST':
        form = AccountTypeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de conta selecionado com sucesso!')
            return redirect('complete_profile')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = AccountTypeForm(instance=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/choose_account_type.html', context)


def complete_profile(request):
    """
    Permite ao usuário completar seu perfil após escolher o tipo de conta.
    
    Exibe formulário específico para cliente ou restaurante com base
    no tipo de conta selecionado.
    """
    if not request.user.role:
        messages.warning(request, 'Por favor, escolha o tipo de conta primeiro.')
        return redirect('choose_account_type')
        
    profile = UserProfile.objects.get_or_create(user=request.user)[0]
    
    if request.method == 'POST':
        if request.user.role == User.RESTAURANT:
            form = RestaurantProfileForm(request.POST, request.FILES, instance=profile)
        else:
            form = CustomerProfileForm(request.POST, request.FILES, instance=profile)
            
        if form.is_valid():
            # Atualizar perfil
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            
            # Atualizar usuário
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.phone_number = form.cleaned_data['phone_number']
            user.save()
            
            # Criar vendor se for restaurante
            if request.user.role == User.RESTAURANT:
                vendor_name = form.cleaned_data.get('vendor_name', f"{user.first_name}'s Restaurant")
                vendor = Vendor.objects.get_or_create(
                    user=user,
                    user_profile=profile,
                    defaults={
                        'vendor_name': vendor_name,
                        'vendor_slug': slugify(vendor_name),
                        'is_approved': False,
                        'is_open': True
                    }
                )[0]
                
                # Se já existia, atualizar nome
                if 'vendor_name' in form.cleaned_data:
                    vendor.vendor_name = form.cleaned_data['vendor_name']
                    vendor.vendor_slug = slugify(form.cleaned_data['vendor_name'])
                    vendor.save()
            
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('myAccount')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        if request.user.role == User.RESTAURANT:
            form = RestaurantProfileForm(instance=profile, initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'phone_number': request.user.phone_number,
            })
            
            # Tentar obter vendor_name se existir
            try:
                vendor = Vendor.objects.get(user=request.user)
                form.fields['vendor_name'].initial = vendor.vendor_name
            except Vendor.DoesNotExist:
                pass
        else:
            form = CustomerProfileForm(instance=profile, initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'phone_number': request.user.phone_number,
            })
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'accounts/complete_profile.html', context)


@login_required(login_url='request_otp')
def myAccount(request):
    """
    Redireciona o usuário para o dashboard apropriado com base no tipo de conta.
    """
    if request.user.role == User.RESTAURANT:
        return redirect('vendorDashboard')
    elif request.user.role == User.CUSTOMER:
        return redirect('custDashboard')
    else:
        # Se o tipo de conta não foi definido
        return redirect('choose_account_type')


@login_required(login_url='request_otp')
def edit_profile(request):
    """
    Permite ao usuário editar seu perfil.
    
    Exibe formulário específico para cliente ou restaurante com base
    no tipo de conta do usuário.
    """
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        if request.user.role == User.RESTAURANT:
            form = RestaurantProfileForm(request.POST, request.FILES, instance=profile)
        else:
            form = CustomerProfileForm(request.POST, request.FILES, instance=profile)
            
        if form.is_valid():
            # Atualizar perfil
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            
            # Atualizar usuário
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.phone_number = form.cleaned_data['phone_number']
            user.save()
            
            # Atualizar vendor se for restaurante
            if request.user.role == User.RESTAURANT and 'vendor_name' in form.cleaned_data:
                try:
                    vendor = Vendor.objects.get(user=request.user)
                    vendor.vendor_name = form.cleaned_data['vendor_name']
                    vendor.vendor_slug = slugify(form.cleaned_data['vendor_name'])
                    vendor.save()
                except Vendor.DoesNotExist:
                    pass
            
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('edit_profile')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        if request.user.role == User.RESTAURANT:
            form = RestaurantProfileForm(instance=profile, initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'phone_number': request.user.phone_number,
            })
            
            # Tentar obter vendor_name se existir
            try:
                vendor = Vendor.objects.get(user=request.user)
                form.fields['vendor_name'].initial = vendor.vendor_name
            except Vendor.DoesNotExist:
                pass
        else:
            form = CustomerProfileForm(instance=profile, initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'phone_number': request.user.phone_number,
            })
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url='request_otp')
@user_passes_test(check_role_customer, login_url='request_otp')
def custDashboard(request):
    """
    Exibe o dashboard do cliente com pedidos e informações relevantes.
    """
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    recent_orders = orders[:5]  # Últimos 5 pedidos
    
    context = {
        'orders': recent_orders,
        'order_count': orders.count(),
    }
    return render(request, 'accounts/custDashboard.html', context)


@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def vendorDashboard(request):
    """
    Exibe o dashboard do restaurante com pedidos, receitas e estatísticas.
    """
    try:
        vendor = Vendor.objects.get(user=request.user)
        
        # Filtrar pedidos por status
        status_filter = request.GET.get('status')
        orders = Order.objects.filter(vendors__in=[vendor.id]).order_by('-created_at')
        
        if status_filter and status_filter != 'all':
            orders = orders.filter(status=status_filter)
        
        # Limitar a 10 pedidos recentes
        orders_list = orders[:10]
        
        # Estatísticas
        total_orders = orders.count()
        
        # Calcular receita total
        total_revenue = orders.aggregate(
            total=Sum('order_total')
        )['total'] or 0
        
        # Calcular receita mensal
        current_month = timezone.now().month
        monthly_revenue = orders.filter(
            created_at__month=current_month
        ).aggregate(
            total=Sum('order_total')
        )['total'] or 0
        
        # Opções de status para filtro
        status_choices = Order._meta.get_field('status').choices
        
        context = {
            'vendor': vendor,
            'orders': orders_list,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'status_choices': status_choices,
            'current_filter': status_filter or 'all'
        }
        return render(request, 'accounts/vendorDashboard.html', context)
    except Vendor.DoesNotExist:
        # Se o vendor não existir, redirecionar para completar o perfil
        messages.error(request, 'Perfil de restaurante não encontrado. Por favor, complete seu cadastro.')
        return redirect(reverse('complete_profile'))


@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def restaurant_profile(request):
    """
    Permite ao restaurante editar seu perfil e status de funcionamento.
    
    Exibe formulário para edição de dados do restaurante, incluindo
    status aberto/fechado, endereço, fotos e informações básicas.
    """
    try:
        vendor = Vendor.objects.get(user=request.user)
        profile = request.user.userprofile
        
        if request.method == 'POST':
            form = RestaurantProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                # Atualizar perfil
                profile = form.save(commit=False)
                profile.user = request.user
                profile.save()
                
                # Atualizar usuário
                user = request.user
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.phone_number = form.cleaned_data['phone_number']
                user.save()
                
                # Atualizar vendor
                vendor.vendor_name = form.cleaned_data['vendor_name']
                vendor.vendor_slug = slugify(form.cleaned_data['vendor_name'])
                vendor.is_open = form.cleaned_data['is_open']
                vendor.save()
                
                messages.success(request, 'Perfil do restaurante atualizado com sucesso!')
                return redirect('restaurant_profile')
            else:
                messages.error(request, 'Por favor, corrija os erros no formulário.')
        else:
            form = RestaurantProfileForm(instance=profile, initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'phone_number': request.user.phone_number,
                'vendor_name': vendor.vendor_name,
                'is_open': vendor.is_open
            })
        
        context = {
            'form': form,
            'profile': profile,
            'vendor': vendor
        }
        return render(request, 'accounts/restaurant_profile.html', context)
    except Vendor.DoesNotExist:
        messages.error(request, 'Perfil de restaurante não encontrado. Por favor, complete seu cadastro.')
        return redirect(reverse('complete_profile'))


# --- Redirecionamentos para OTP (em caso de esquecimento) ---
def forgot_password(request):
    return redirect(reverse('request_otp'))

def reset_password_validate(request, uidb64, token):
    return redirect(reverse('request_otp'))

def reset_password(request):
    return redirect(reverse('request_otp'))
