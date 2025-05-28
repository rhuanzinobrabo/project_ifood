from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.urls import reverse
from django.utils.crypto import get_random_string
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator


# Imports para autenticação social
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView, OAuth2CallbackView

from .utils import detectUser
from .forms import EmailForm, OTPForm, AccountTypeForm, CustomerProfileForm, RestaurantProfileForm, UserForm, UserProfileForm, UserAddressForm, UserAddress
from .models import User, UserProfile, OTPModel
from vendor.forms import VendorForm
from vendor.models import Vendor

# --- Funções auxiliares ---

def check_role_vendor(user):
    if user.role == 1:
        return True
    messages.error(user, 'Acesso restrito. Somente restaurantes podem acessar esta área.')
    return False

def check_role_customer(user):
    if user.role == 2:
        return True
    messages.error(user, 'Acesso restrito. Somente clientes podem acessar esta área.')
    return False

def check_role_admin(user):
    if user.is_superuser:
        return True
    messages.error(user, 'Acesso restrito. Somente administradores podem acessar esta área.')
    return False

def detectUser(user):
    if user.role == 1:
        return 'vendorDashboard'
    elif user.role == 2:
        return 'custDashboard'
    elif user.is_superuser:
        return 'admin_dashboard'
    return 'myAccount'

def send_otp_via_email(email):
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
    messages.info(request, 'Cadastre-se via OTP ou login social.')
    return redirect('social_login')

def registerVendor(request):
    messages.info(request, 'Cadastre-se via OTP ou login social.')
    return redirect('social_login')

def login(request):
    return redirect('social_login')

def logout(request):
    auth.logout(request)
    messages.info(request, 'Sessão finalizada com êxito.')
    return redirect('social_login')

@login_required(login_url='social_login')
def myAccount(request):
    user = request.user
    if user.role == 1:
        return redirect('vendorDashboard')
    elif user.role == 2:
        return redirect('custDashboard')
    elif user.is_superuser:
        return redirect('admin_dashboard')
    else:
        messages.info(request, 'Complete seu cadastro.')
        return redirect('choose_account_type')

@login_required(login_url='social_login')
@user_passes_test(check_role_customer)
def custDashboard(request):
    profile = UserProfile.objects.get(user=request.user)

    orders = [
        {'id': '22606', 'date': 'Apr 9, 2020', 'total': '38.99', 'charges': '3.90', 'received': '35.09', 'status': 'Completed'},
        {'id': '22583', 'date': 'Apr 9, 2020', 'total': '26.22', 'charges': '2.62', 'received': '23.60', 'status': 'Processing'},
        {'id': '22493', 'date': 'Apr 2, 2020', 'total': '28.24', 'charges': '2.82', 'received': '25.42', 'status': 'Completed'},
    ]

    context = {
        'user': request.user,
        'profile': profile,
        'orders': orders,
    }
    return render(request, 'accounts/custDashboard.html', context)

@login_required(login_url='social_login')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    return render(request, 'accounts/vendorDashboard.html')

# --- Redirecionamentos para OTP (em caso de esquecimento) ---

def forgot_password(request):
    messages.info(request, 'Login e recuperação de senha agora funcionam via OTP ou login social.')
    return redirect('social_login')

def reset_password_validate(request, uidb64, token):
    return redirect('social_login')

def reset_password(request):
    return redirect('social_login')

# --- CRUD de Endereços ---

@login_required(login_url='social_login')
def address_list(request):
    """
    Lista todos os endereços do usuário logado
    """
    addresses = UserAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    
    search_query = request.GET.get('search', '')
    if search_query:
        addresses = addresses.filter(
            Q(address_line1__icontains=search_query) | 
            Q(city__icontains=search_query) |
            Q(state__icontains=search_query)
        )
    
    # Paginação
    paginator = Paginator(addresses, 5)  # 5 endereços por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'addresses': page_obj,
        'search_query': search_query,
    }
    return render(request, 'accounts/address_list.html', context)

@login_required(login_url='social_login')
def address_create(request):
    """
    Cria um novo endereço para o usuário logado
    """
    if request.method == 'POST':
        form = UserAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            
            messages.success(request, 'Endereço adicionado com sucesso!')
            return redirect('address_list')
    else:
        form = UserAddressForm()
    
    context = {
        'form': form,
        'title': 'Adicionar Novo Endereço',
    }
    return render(request, 'accounts/address_form.html', context)

@login_required(login_url='social_login')
def address_update(request, pk):
    """
    Atualiza um endereço existente
    """
    address = get_object_or_404(UserAddress, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = UserAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            
            messages.success(request, 'Endereço atualizado com sucesso!')
            return redirect('address_list')
    else:
        form = UserAddressForm(instance=address)
    
    context = {
        'form': form,
        'address': address,
        'title': 'Editar Endereço',
    }
    return render(request, 'accounts/address_form.html', context)

@login_required(login_url='social_login')
def address_delete(request, pk):
    """
    Exclui um endereço
    """
    address = get_object_or_404(UserAddress, pk=pk, user=request.user)
    
    if request.method == 'POST':
        was_default = address.is_default
        address.delete()
        
        # Se o endereço excluído era o padrão, defina outro como padrão
        if was_default:
            remaining = UserAddress.objects.filter(user=request.user).first()
            if remaining:
                remaining.is_default = True
                remaining.save()
        
        messages.success(request, 'Endereço excluído com sucesso!')
        return redirect('address_list')
    
    context = {
        'address': address,
    }
    return render(request, 'accounts/address_delete.html', context)

@login_required(login_url='social_login')
def set_default_address(request, pk):
    """
    Define um endereço como padrão
    """
    address = get_object_or_404(UserAddress, pk=pk, user=request.user)
    
    # Remover status padrão de todos os endereços do usuário
    UserAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
    
    # Definir este endereço como padrão
    address.is_default = True
    address.save()
    
    messages.success(request, 'Endereço definido como padrão com sucesso!')
    return redirect('address_list')