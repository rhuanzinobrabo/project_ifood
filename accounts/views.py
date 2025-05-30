# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.urls import reverse # Importar reverse
from django.utils.crypto import get_random_string
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.template.defaultfilters import slugify # Importar slugify

# Removido import de utils, pois detectUser está aqui
from .forms import EmailForm, OTPForm, AccountTypeForm, CustomerProfileForm, RestaurantProfileForm
from .models import User, UserProfile, OTPModel
# Removido import desnecessário de VendorForm
from vendor.models import Vendor # Importar Vendor

# --- Funções auxiliares ---

def check_role_vendor(user):
    if user.role == User.RESTAURANT: # Usar constante do modelo
        return True
    # A mensagem de erro deve ser adicionada na view que chama o teste
    return False

def check_role_customer(user):
    if user.role == User.CUSTOMER: # Usar constante do modelo
        return True
    # A mensagem de erro deve ser adicionada na view que chama o teste
    return False

# ADICIONADO: Função para verificar se é admin/superuser
def check_role_admin(user):
    if user.is_superuser:
        return True
    # A mensagem de erro deve ser adicionada na view que chama o teste
    return False

def detectUser(user):
    if user.is_superuser:
        # Idealmente, admin teria um dashboard próprio
        # Verifique se existe uma URL como 'admin_dashboard'
        # return 'admin_dashboard' 
        return 'home' # Fallback para home
    elif user.role == User.RESTAURANT:
        return 'vendorDashboard'
    elif user.role == User.CUSTOMER:
        return 'custDashboard'
    # Se não for superuser e não tiver role definido, vai para escolher tipo
    return 'choose_account_type'

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
    # Tratamento de erro básico para envio de email
    try:
        send_mail(
            subject='Seu código de verificação',
            message=f'Seu código OTP é: {otp}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        # Logar o erro seria ideal aqui
        print(f"Erro ao enviar OTP para {email}: {e}")
        # Você pode querer levantar uma exceção ou retornar False
        pass # Por enquanto, falha silenciosamente no caso de erro

# --- Views principais ---

def request_otp(request):
    if request.user.is_authenticated:
        return redirect(detectUser(request.user)) # Redireciona se já logado
        
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            send_otp_via_email(email) # Função já trata erro básico
            request.session['otp_email'] = email
            messages.success(request, 'Enviamos um código para seu e-mail.')
            # Usar reverse para obter a URL
            return redirect(reverse('verify_otp')) 
    else:
        form = EmailForm()
    return render(request, 'accounts/request_otp.html', {'form': form})

def verify_otp(request):
    if request.user.is_authenticated:
        return redirect(detectUser(request.user)) # Redireciona se já logado
        
    email = request.session.get('otp_email')
    if not email:
        messages.error(request, 'Sessão expirada ou inválida. Por favor, solicite um novo código.')
        return redirect(reverse('request_otp'))

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            try:
                otp_record = OTPModel.objects.get(email=email)

                if otp_record.is_blocked(): # Usar método do modelo
                    messages.error(request, 'Muitas tentativas. Tente novamente em alguns minutos.')
                    return redirect(reverse('verify_otp'))

                if otp_record.is_expired(): # Usar método do modelo
                    otp_record.delete()
                    messages.error(request, 'O código expirou. Solicite um novo.')
                    return redirect(reverse('request_otp'))

                if otp_record.otp == entered_otp:
                    user, created = User.objects.get_or_create(
                        email=email, 
                        defaults={'username': User.objects.generate_username(email)}
                    )

                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    auth.login(request, user)

                    otp_record.delete()
                    if 'otp_email' in request.session:
                        del request.session['otp_email'] # Limpa a sessão

                    messages.success(request, 'Login efetuado com sucesso!')
                    return redirect(detectUser(user))

                # OTP incorreto
                otp_record.attempts += 1
                if otp_record.attempts >= 5:
                    otp_record.blocked_until = timezone.now() + timedelta(minutes=10)
                    messages.error(request, 'Muitas tentativas. Bloqueado por 10 minutos.')
                else:
                    messages.error(request, f'Código incorreto. Tentativas restantes: {5 - otp_record.attempts}')
                otp_record.save()
                return redirect(reverse('verify_otp'))

            except OTPModel.DoesNotExist:
                messages.error(request, 'Código inválido ou expirado. Solicite um novo.')
                return redirect(reverse('request_otp'))
    else:
        form = OTPForm()
    return render(request, 'accounts/verify_otp.html', {'form': form})

@login_required(login_url='request_otp')
def choose_account_type(request):
    user = request.user
    if user.role or user.is_superuser:
        return redirect(detectUser(user))

    if request.method == 'POST':
        form = AccountTypeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect(reverse('complete_profile'))
    else:
        form = AccountTypeForm(instance=user)

    return render(request, 'accounts/choose_account_type.html', {'form': form})

@login_required(login_url='request_otp')
def complete_profile(request):
    user = request.user

    if not user.role and not user.is_superuser:
        return redirect(reverse('choose_account_type'))
    
    if user.is_superuser:
         messages.info(request, 'Administradores não completam perfil por esta tela.')
         return redirect(reverse('home'))

    profile, created = UserProfile.objects.get_or_create(user=user)
    ProfileForm = RestaurantProfileForm if user.role == User.RESTAURANT else CustomerProfileForm

    if request.method == 'POST':
        # Atualiza User (first_name, last_name)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        # Adicione validação se necessário
        
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if profile_form.is_valid():
            user.save() 
            profile_form.save()

            if user.role == User.RESTAURANT and not hasattr(user, 'vendor'):
                Vendor.objects.create(
                    user=user,
                    user_profile=profile,
                    vendor_name=f'{user.first_name} {user.last_name}' or user.username,
                    vendor_slug=slugify(user.username),
                )

            messages.success(request, 'Cadastro completo com sucesso!')
            return redirect(detectUser(user))
        else:
             messages.error(request, 'Erro ao salvar perfil. Verifique os campos.')
    else:
        profile_form = ProfileForm(instance=profile)

    return render(request, 'accounts/complete_profile.html', {
        'profile_form': profile_form,
        'user': user 
    })

# --- Fluxos auxiliares ---

def registerUser(request):
    return redirect(reverse('request_otp'))

def registerVendor(request):
    return redirect(reverse('request_otp'))

def login(request):
    return redirect(reverse('request_otp'))

def logout(request):
    auth.logout(request)
    messages.info(request, 'Sessão finalizada com êxito.')
    return redirect(reverse('home'))

@login_required(login_url='request_otp')
def myAccount(request):
    return redirect(detectUser(request.user))

@login_required(login_url='request_otp')
@user_passes_test(check_role_customer, login_url='request_otp') # Adicionar login_url ao user_passes_test
def custDashboard(request):
    # Adicionar mensagem de erro se check_role falhar
    if not check_role_customer(request.user):
        messages.error(request, 'Acesso restrito. Somente clientes podem acessar esta área.')
        return redirect(reverse('home')) # Ou outra página apropriada
        
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None
        messages.warning(request, 'Perfil não encontrado. Por favor, complete seu cadastro.')
        # return redirect(reverse('complete_profile'))

    # Implementar busca de pedidos reais
    orders = [] 

    context = {
        'profile': profile,
        'orders': orders,
    }
    return render(request, 'accounts/custDashboard.html', context)

@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    try:
        # Obter o vendor associado ao usuário atual
        vendor = Vendor.objects.get(user=request.user)
        context = {
            'vendor': vendor,
        }
        return render(request, 'accounts/vendorDashboard.html', context)
    except Vendor.DoesNotExist:
        # Se o vendor não existir, redirecionar para uma página apropriada
        messages.error(request, 'Perfil de restaurante não encontrado.')
        return redirect('myAccount')

# --- Redirecionamentos para OTP (em caso de esquecimento) ---
def forgot_password(request):
    return redirect(reverse('request_otp'))

def reset_password_validate(request, uidb64, token):
    return redirect(reverse('request_otp'))

def reset_password(request):
    return redirect(reverse('request_otp'))

