from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.urls import reverse
from django.utils.crypto import get_random_string
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

from .utils import detectUser
from .forms import EmailForm, OTPForm, AccountTypeForm, CustomerProfileForm, RestaurantProfileForm
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

def detectUser(user):
    if user.role == 1:
        return 'vendorDashboard'
    elif user.role == 2:
        return 'custDashboard'

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

# --- Fluxos auxiliares ---

def registerUser(request):
    messages.info(request, 'Cadastre-se via OTP.')
    return redirect('request_otp')

def registerVendor(request):
    messages.info(request, 'Cadastre-se via OTP.')
    return redirect('request_otp')

def login(request):
    return redirect('request_otp')

def logout(request):
    auth.logout(request)
    messages.info(request, 'Sessão finalizada com êxito.')
    return redirect('request_otp')

@login_required(login_url='request_otp')
def myAccount(request):
    user = request.user
    if user.role == 1:
        return redirect('vendorDashboard')
    elif user.role == 2:
        return redirect('custDashboard')
    else:
        messages.info(request, 'Complete seu cadastro.')
        return redirect('choose_account_type')

@login_required(login_url='request_otp')
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

@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    return render(request, 'accounts/vendorDashboard.html')

# --- Redirecionamentos para OTP (em caso de esquecimento) ---

def forgot_password(request):
    messages.info(request, 'Login e recuperação de senha agora funcionam via OTP.')
    return redirect('request_otp')

def reset_password_validate(request, uidb64, token):
    return redirect('request_otp')

def reset_password(request):
    return redirect('request_otp')
