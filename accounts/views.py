import datetime
import random
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone

from accounts.forms import AccountTypeForm, EmailForm, OTPForm, UserForm, UserProfileForm
from accounts.models import User, UserProfile
from accounts.utils import check_role_customer, check_role_vendor, send_otp_email
from marketplace.models import Order
from vendor.models import Vendor

def request_otp(request):
    """
    Exibe formulário para solicitar código OTP via email.
    """
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                otp = ''.join(random.choices('0123456789', k=6))
                user.otp = otp
                user.otp_expiry = timezone.now() + datetime.timedelta(minutes=10)
                user.save()
                mail_subject = 'Código de Verificação para Login'
                email_template = 'accounts/emails/otp_email.html'
                # send_otp_email(user, mail_subject, email_template)
                messages.success(request, 'Código de verificação enviado para seu email.')
                return redirect('verify_otp')
            else:
                user = User.objects.create_user(email=email)
                user.set_unusable_password()
                otp = ''.join(random.choices('0123456789', k=6))
                user.otp = otp
                user.otp_expiry = timezone.now() + datetime.timedelta(minutes=10)
                user.save()
                mail_subject = 'Código de Verificação para Cadastro'
                email_template = 'accounts/emails/otp_email.html'
                # send_otp_email(user, mail_subject, email_template)
                messages.success(request, 'Código de verificação enviado para seu email.')
                return redirect('verify_otp')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = EmailForm()
    
    context = {'form': form}
    return render(request, 'accounts/request_otp.html', context)

def verify_otp(request):
    """
    Verifica o código OTP fornecido pelo usuário.
    """
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            users = User.objects.filter(otp=otp)
            if users.exists():
                user = users.first()
                user.otp = None
                user.otp_expiry = None
                user.save()
                auth.login(request, user)
                if not user.role:
                    messages.info(request, 'Por favor, escolha o tipo de conta.')
                    return redirect('choose_account_type')
                try:
                    profile = UserProfile.objects.get(user=user)
                    if not profile.address_line_1:
                        messages.info(request, 'Por favor, complete seu perfil.')
                        return redirect('complete_profile')
                except UserProfile.DoesNotExist:
                    messages.info(request, 'Por favor, complete seu perfil.')
                    return redirect('complete_profile')
                return redirect('myAccount')
            else:
                messages.error(request, 'Código inválido ou expirado.')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = OTPForm()
    
    context = {'form': form}
    return render(request, 'accounts/verify_otp.html', context)

def registerUser(request):
    return redirect('request_otp')

def registerVendor(request):
    return redirect('request_otp')

def login(request):
    return redirect('request_otp')

def logout(request):
    auth.logout(request)
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('request_otp')

def choose_account_type(request):
    """
    Permite ao usuário escolher o tipo de conta (Cliente ou Restaurante).
    """
    if request.user.is_authenticated and request.user.role:
        messages.warning(request, 'Você já escolheu o tipo de conta.')
        return redirect('myAccount')
        
    if request.method == 'POST':
        form = AccountTypeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de conta selecionado com sucesso!')
            return redirect('complete_profile')
        else:
            messages.error(request, 'Por favor, selecione um tipo de conta.')
    else:
        form = AccountTypeForm(instance=request.user)
    
    context = {'form': form}
    return render(request, 'accounts/choose_account_type.html', context)

def complete_profile(request):
    """
    Permite ao usuário completar seu perfil usando UserForm e UserProfileForm.
    """
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Perfil completado com sucesso!')
            return redirect('myAccount')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    }
    return render(request, 'accounts/complete_profile.html', context)

@login_required(login_url='request_otp')
def myAccount(request):
    """
    Redireciona o usuário para o dashboard apropriado com base no tipo de conta.
    """
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if not user.role:
        messages.info(request, 'Por favor, escolha o tipo de conta.')
        return redirect('choose_account_type')
    
    if not profile.address_line_1:
        messages.info(request, 'Por favor, complete seu perfil.')
        return redirect('complete_profile')
    
    if user.role == User.RESTAURANT:
        return redirect('vendorDashboard')
    elif user.role == User.CUSTOMER:
        return redirect('custDashboard')
    else:
        messages.error(request, 'Erro: Tipo de conta inválido.')
        return redirect('home')

@login_required(login_url='request_otp')
def edit_profile(request):
    """
    Permite ao usuário editar seu perfil usando UserForm e UserProfileForm.
    """
    profile = get_object_or_404(UserProfile, user=request.user)
    user = request.user

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('edit_profile')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='request_otp')
@user_passes_test(check_role_customer, login_url='request_otp')
def custDashboard(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    recent_orders = orders[:5]
    
    context = {
        'orders': recent_orders,
        'order_count': orders.count(),
    }
    return render(request, 'accounts/custDashboard.html', context)

@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def vendorDashboard(request):
    try:
        vendor = Vendor.objects.get(user=request.user)
        orders = Order.objects.filter(vendors__in=[vendor.id], is_ordered=True).order_by('-created_at')
        
        status_filter = request.GET.get('status')
        if status_filter and status_filter != 'all':
            orders = orders.filter(status=status_filter)
            
        orders_list = orders[:10]
        total_orders = orders.count()
        
        total_revenue = orders.aggregate(total=Sum('order_total'))['total'] or 0
        
        current_month = timezone.now().month
        monthly_revenue = orders.filter(created_at__month=current_month).aggregate(total=Sum('order_total'))['total'] or 0
        
        status_choices = Order._meta.get_field('status').choices
        
        context = {
            'vendor': vendor,
            'orders': orders_list,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'status_choices': status_choices,
            'current_status_filter': status_filter if status_filter else 'all',
        }
        return render(request, 'accounts/vendorDashboard.html', context)
    except Vendor.DoesNotExist:
        messages.error(request, 'Perfil de restaurante não encontrado.')
        return redirect('myAccount')

@login_required(login_url='request_otp')
@user_passes_test(check_role_vendor, login_url='request_otp')
def restaurant_profile(request):
    messages.info(request, 'Gerenciamento do perfil do restaurante agora em Meu Perfil.')
    return redirect('edit_profile')