"""
Arquivo: accounts/views.py
Descrição: Contém todas as views relacionadas a contas de usuário, incluindo:
- Autenticação (login, registro, logout)
- Gerenciamento de perfil
- Verificação de email e OTP
- Administração de usuários
- Integração com login social
- Gerenciamento de endereços

Dependências principais:
- accounts/models.py: Modelos de usuário, perfil e endereço
- accounts/forms.py: Formulários para manipulação de dados de usuário
- accounts/utils.py: Funções utilitárias para notificações e verificações
"""

# Imports do Django
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator

# Imports da biblioteca padrão Python
from datetime import timedelta

# Imports para autenticação social
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView, OAuth2CallbackView

# Imports locais (do próprio projeto )
from .utils import detectUser
from .forms import EmailForm, OTPForm, AccountTypeForm, CustomerProfileForm, RestaurantProfileForm, UserForm, UserProfileForm, UserAddressForm, UserAddress
from .models import User, UserProfile, OTPModel, UserAddress
from vendor.forms import VendorForm
from vendor.models import Vendor

# --- Funções auxiliares ---

def check_role_vendor(user):
    """
    Verifica se o usuário tem papel de restaurante.
    
    Args:
        user: Instância do modelo User
        
    Returns:
        bool: True se o usuário é restaurante, False caso contrário
    """
    if user.role == 1:
        return True
    messages.error(user, 'Acesso restrito. Somente restaurantes podem acessar esta área.')
    return False

def check_role_customer(user):
    """
    Verifica se o usuário tem papel de cliente.
    
    Args:
        user: Instância do modelo User
        
    Returns:
        bool: True se o usuário é cliente, False caso contrário
    """
    if user.role == 2:
        return True
    messages.error(user, 'Acesso restrito. Somente clientes podem acessar esta área.')
    return False

def check_role_admin(user):
    """
    Verifica se o usuário é administrador.
    
    Args:
        user: Instância do modelo User
        
    Returns:
        bool: True se o usuário é administrador, False caso contrário
    """
    if user.is_superuser:
        return True
    messages.error(user, 'Acesso restrito. Somente administradores podem acessar esta área.')
    return False

def detectUser(user):
    """
    Detecta o tipo de usuário e retorna a URL de redirecionamento apropriada.
    
    Args:
        user: Instância do modelo User
        
    Returns:
        str: URL para redirecionamento baseada no papel do usuário
    """
    if user.role == 1:
        return 'vendorDashboard'
    elif user.role == 2:
        return 'custDashboard'
    elif user.is_superuser:
        return 'admin_dashboard'
    return 'myAccount'

def send_otp_via_email(email):
    """
    Gera e envia um código OTP para o email fornecido.
    
    Args:
        email: Email do usuário para envio do OTP
    """
    otp = get_random_string(length=6, allowed_chars='1234567890')
    OTPModel.objects.update_or_create(
        email=email,
        defaults={
            'otp': otp,
            'created_at': timezone.now(),
            'attempts': 0,
            'blocked_until': None,
        }
    )
    send_mail(
        subject='Seu código de verificação',
        message=f'Seu código OTP é: {otp}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

def social_login(request):
    """
    Página com opções de login social (Facebook e Google)
    """
    return render(request, 'accounts/social_login.html')

def social_callback(request):
    """
    Callback para processamento após autenticação social
    """
    if request.user.is_authenticated:
        user = request.user
        
        # Verificar se é um novo usuário ou se precisa completar o perfil
        if not user.first_name or not user.last_name or not user.role:
            messages.info(request, 'Complete seu cadastro para continuar.')
            return redirect('choose_account_type')
        
        messages.success(request, 'Login social efetuado com sucesso!')
        return redirect(detectUser(user))
    
    messages.error(request, 'Falha na autenticação social. Tente novamente.')
    return redirect('social_login')

# --- Views principais ---

def request_otp(request):
    """
    Solicita email para envio de código OTP
    """
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            send_otp_via_email(email)
            request.session['otp_email'] = email
            messages.success(request, 'Enviamos um código para seu e-mail.')
            return redirect('verify_otp')
    else:
        form = EmailForm()
    return render(request, 'accounts/request_otp.html', {'form': form})

def verify_otp(request):
    """
    Verifica o código OTP enviado por email
    """
    email = request.session.get('otp_email')
    if not email:
        return redirect('request_otp')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            try:
                otp_record = OTPModel.objects.get(email=email)

                if otp_record.blocked_until and timezone.now() < otp_record.blocked_until:
                    messages.error(request, 'Muitas tentativas. Tente novamente em alguns minutos.')
                    return redirect('verify_otp')

                if timezone.now() > otp_record.created_at + timedelta(minutes=5):
                    otp_record.delete()
                    messages.error(request, 'O código expirou. Solicite um novo.')
                    return redirect('request_otp')

                if otp_record.otp == entered_otp:
                    user, created = User.objects.get_or_create(username=email, defaults={'email': email})

                    # ✅ Define o backend manualmente
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    auth.login(request, user)

                    otp_record.delete()

                    if user.first_name and user.last_name and user.role:
                        messages.success(request, 'Login efetuado com sucesso!')
                        return redirect(detectUser(user))
                    else:
                        messages.info(request, 'Complete seu cadastro para continuar.')
                        return redirect('choose_account_type')

                # OTP incorreto
                otp_record.attempts += 1
                if otp_record.attempts >= 5:
                    otp_record.blocked_until = timezone.now() + timedelta(minutes=10)
                    messages.error(request, 'Muitas tentativas. Bloqueado por 10 minutos.')
                else:
                    messages.error(request, f'Código incorreto. Tentativas restantes: {5 - otp_record.attempts}')
                otp_record.save()
                return redirect('verify_otp')

            except OTPModel.DoesNotExist:
                messages.error(request, 'Código inválido.')
                return redirect('verify_otp')
    else:
        form = OTPForm()
    return render(request, 'accounts/verify_otp.html', {'form': form})

@login_required(login_url='request_otp')
def choose_account_type(request):
    """
    Permite ao usuário escolher o tipo de conta (cliente ou restaurante)
    """
    user = request.user
    if user.role:
        return redirect('complete_profile')

    if request.method == 'POST':
        form = AccountTypeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('complete_profile')
    else:
        form = AccountTypeForm(instance=user)

    return render(request, 'accounts/choose_account_type.html', {'form': form})

@login_required(login_url='request_otp')
def complete_profile(request):
    """
    Permite ao usuário completar seu perfil após escolher o tipo de conta
    """
    user = request.user

    if not user.role:
        return redirect('choose_account_type')

    ProfileForm = RestaurantProfileForm if user.role == 1 else CustomerProfileForm

    if request.method == 'POST':
        user_form = AccountTypeForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=user.userprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            # ✅ Se for restaurante, cria Vendor automaticamente
            if user.role == 1 and not Vendor.objects.filter(user=user).exists():
                vendor = Vendor.objects.create(
                    user=user,
                    user_profile=user.userprofile,  # Garantir que o UserProfile esteja atribuído
                    vendor_name=f"{user.first_name} {user.last_name}",
                    vendor_slug=user.username,
                    vendor_license='PENDENTE',  # Você pode atualizar isso conforme necessário
                )

            messages.success(request, 'Cadastro completo com sucesso!')
            return redirect(detectUser(user))
    else:
        user_form = AccountTypeForm(instance=user)
        profile_form = ProfileForm(instance=user.userprofile)

    return render(request, 'accounts/complete_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })

# --- CRUD de Contas (Implementação Completa) ---

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin)
def admin_dashboard(request):
    """
    Dashboard administrativo com estatísticas e ações rápidas
    """
    total_users = User.objects.count()
    total_customers = User.objects.filter(role=2).count()
    total_vendors = User.objects.filter(role=1).count()
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    context = {
        'total_users': total_users,
        'total_customers': total_customers,
        'total_vendors': total_vendors,
        'recent_users': recent_users,
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin)
def user_list(request):
    """
    Lista todos os usuários (CREATE - Read - Update - Delete)
    """
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all().order_by('-date_joined')
    
    # Aplicar filtros se fornecidos
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'accounts/user_list.html', context)

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin)
def user_create(request):
    """
    Cria um novo usuário (Create - READ - Update - Delete)
    """
    if request.method == 'POST':
        # Extrair dados do formulário
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        role = request.POST.get('role')
        password = request.POST.get('password')
        
        # Validar dados
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email já cadastrado.')
            return redirect('user_create')
        
        if not username:
            username = email.split('@')[0]
            
            # Garantir username único
            counter = 1
            temp_username = username
            while User.objects.filter(username=temp_username).exists():
                temp_username = f"{username}{counter}"
                counter += 1
            username = temp_username
        
        # Criar usuário
        user = User.objects.create_user(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.role = role
        user.save()
        
        messages.success(request, f'Usuário {email} criado com sucesso!')
        return redirect('user_detail', pk=user.pk)
    
    return render(request, 'accounts/user_create.html')

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin)
def user_detail(request, pk):
    """
    Exibe detalhes de um usuário (Create - Read - UPDATE - Delete)
    """
    user = get_object_or_404(User, pk=pk)
    profile = UserProfile.objects.get(user=user)
    
    context = {
        'user_obj': user,  # Renomeado para evitar conflito com request.user
        'profile': profile,
    }
    return render(request, 'accounts/user_detail.html', context)

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin)
def user_update(request, pk):
    """
    Atualiza um usuário existente (Create - Read - Update - DELETE)
    """
    user = get_object_or_404(User, pk=pk)
    profile = UserProfile.objects.get(user=user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            messages.success(request, f'Usuário {user.email} atualizado com sucesso!')
            return redirect('user_detail', pk=user.pk)
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_obj': user,  # Renomeado para evitar conflito
        'profile': profile,
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/user_update.html', context)

@login_required(login_url='request_otp')
@user_passes_test(check_role_admin)
def user_delete(request, pk):
    """
    Exclui um usuário (Create - Read - Update - DELETE)
    """
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        email = user.email
        user.delete()
        messages.success(request, f'Usuário {email} excluído com sucesso!')
        return redirect('user_list')
    
    context = {
        'user_obj': user,  # Renomeado para evitar conflito
    }
    return render(request, 'accounts/user_delete.html', context)

# --- Perfil do Usuário (Self-service) ---

@login_required(login_url='request_otp')
def profile_view(request):
    """
    Exibe o perfil do usuário logado
    """
    user = request.user
    profile = UserProfile.objects.get(user=user)
    
    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'accounts/profile_view.html', context)

@login_required(login_url='request_otp')
def profile_edit(request):
    """
    Permite ao usuário editar seu próprio perfil
    """
    user = request.user
    profile = UserProfile.objects.get(user=user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('profile_view')
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile_edit.html', context)

@login_required(login_url='request_otp')
def profile_delete(request):
    """
    Permite ao usuário excluir sua própria conta
    """
    user = request.user
    
    if request.method == 'POST':
        password = request.POST.get('password')
        
        # Verificar senha para confirmar exclusão
        if user.check_password(password):
            email = user.email
            auth.logout(request)
            user.delete()
            messages.success(request, f'Conta {email} excluída com sucesso!')
            return redirect('request_otp')
        else:
            messages.error(request, 'Senha incorreta. Exclusão cancelada.')
    
    return render(request, 'accounts/profile_delete.html')

# --- Fluxos auxiliares ---

def registerUser(request):
    """
    Redireciona para o fluxo de registro via OTP ou login social
    """
    messages.info(request, 'Cadastre-se via OTP ou login social.')
    return redirect('social_login')

def registerVendor(request):
    """
    Redireciona para o fluxo de registro de restaurante
    """
    messages.info(request, 'Cadastre-se via OTP ou login social.')
    return redirect('social_login')

def login(request):
    """
    Redireciona para o fluxo de login via OTP ou login social
    """
    messages.info(request, 'Faça login via OTP ou login social.')
    return redirect('social_login')

def logout(request):
    """
    Realiza o logout do usuário
    """
    auth.logout(request)
    messages.success(request, 'Você saiu da sua conta.')
    return redirect('social_login')

@login_required(login_url='request_otp')
def myAccount(request):
    """
    Redireciona para o dashboard apropriado com base no tipo de usuário
    """
    user = request.user
    redirectUrl = detectUser(user)
    return redirect(redirectUrl)

@login_required(login_url='request_otp')
@user_passes_test(check_role_customer)
def custDashboard(request):
    """
    Dashboard para usuários do tipo cliente
    """
    return render(request, 'accounts/custDashboard.html')

@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    """
    Dashboard para usuários do tipo restaurante
    """
    vendor = get_object_or_404(Vendor, user=request.user)
    context = {
        'vendor': vendor,
    }
    return render(request, 'accounts/vendorDashboard.html', context)

# --- CRUD de Endereços ---

@login_required(login_url='request_otp')
def address_list(request):
    """
    Lista todos os endereços do usuário logado
    """
    addresses = UserAddress.objects.filter(user=request.user).order_by('-is_default')
    
    context = {
        'addresses': addresses,
        'title': 'Meus Endereços',
    }
    return render(request, 'accounts/address_list.html', context)

@login_required(login_url='request_otp')
def address_create(request):
    """
    Cria um novo endereço para o usuário logado
    """
    if request.method == 'POST':
        form = UserAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # Se for o primeiro endereço ou is_default estiver marcado
            if UserAddress.objects.filter(user=request.user).count() == 0 or form.cleaned_data.get('is_default'):
                # Desmarcar outros endereços padrão
                UserAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
                address.is_default = True
                
            address.save()
            messages.success(request, 'Endereço adicionado com sucesso!')
            return redirect('address_list')
    else:
        form = UserAddressForm()
    
    context = {
        'form': form,
        'title': 'Adicionar Endereço',
    }
    return render(request, 'accounts/address_form.html', context)

@login_required(login_url='request_otp')
def address_update(request, pk):
    """
    Atualiza um endereço existente do usuário logado
    """
    address = get_object_or_404(UserAddress, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = UserAddressForm(request.POST, instance=address)
        if form.is_valid():
            updated_address = form.save(commit=False)
            
            # Se is_default estiver marcado, desmarcar outros endereços padrão
            if form.cleaned_data.get('is_default'):
                UserAddress.objects.filter(user=request.user, is_default=True).exclude(pk=pk).update(is_default=False)
                updated_address.is_default = True
            
            updated_address.save()
            messages.success(request, 'Endereço atualizado com sucesso!')
            return redirect('address_list')
    else:
        form = UserAddressForm(instance=address)
    
    context = {
        'form': form,
        'title': 'Atualizar Endereço',
        'address': address,
    }
    return render(request, 'accounts/address_form.html', context)

@login_required(login_url='request_otp')
def address_delete(request, pk):
    """
    Exclui um endereço do usuário logado
    """
    address = get_object_or_404(UserAddress, pk=pk, user=request.user)
    
    if request.method == 'POST':
        was_default = address.is_default
        address.delete()
        
        # Se o endereço excluído era o padrão, definir outro como padrão
        if was_default:
            remaining_address = UserAddress.objects.filter(user=request.user).first()
            if remaining_address:
                remaining_address.is_default = True
                remaining_address.save()
        
        messages.success(request, 'Endereço excluído com sucesso!')
        return redirect('address_list')
    
    context = {
        'address': address,
        'title': 'Excluir Endereço',
    }
    return render(request, 'accounts/address_delete.html', context)

@login_required(login_url='request_otp')
def set_default_address(request, pk):
    """
    Define um endereço como padrão para o usuário logado
    """
    address = get_object_or_404(UserAddress, pk=pk, user=request.user)
    
    # Desmarcar o endereço padrão atual
    UserAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
    
    # Definir o novo endereço padrão
    address.is_default = True
    address.save()
    
    messages.success(request, 'Endereço padrão atualizado com sucesso!')
    
    # Redirecionar de volta para a página anterior ou para a lista de endereços
    next_url = request.GET.get('next', 'address_list')
    return HttpResponseRedirect(next_url)