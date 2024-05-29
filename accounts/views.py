from django.shortcuts import render, redirect
from .forms import UserForm
from .models import User, UserProfile
from vendor.forms import VendorForm
from django.contrib import messages, auth
from .utils import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils.http import urlsafe_base64_decode
from vendor.models import Vendor
from django.template.defaultfilters import slugify

#apenas resturante
def check_role_vendor(user):
    if user.role == 1:
        return True
    else: 
        raise PermissionDenied

# apenas cliente
def check_role_customer(user):
    if user.role == 2:
        return True
    else: 
        raise PermissionDenied

# Create your views here.
def registerUser(request):
    if request.user.is_authenticated:
        messages.warning(request, 'Você já está logado!')
        return redirect('dashboard')
     
    elif request.method == 'POST':
        print(request.POST)
        form = UserForm(request.POST)
        if form.is_valid():
            # user = form.save(commit=False)
            # user.role = User.CUSTOMER
            # user.save()

            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
            user.role = User.CUSTOMER
            user.save()

            #parte de mandar o email
            send_verification_email(request, user)

            messages.success(request, 'Parabéns! Sua conta foi criada com sucesso.')
            return redirect('registerUser')
        else: 
            print('formulario enviado é invalido')
            print(form.errors)
    else:
        form = UserForm()
    context = {
        'form':form,
    }
    return render(request, 'accounts/registerUser.html', context)


def registerVendor(request):
    if request.method == 'POST':
        #armazena as infromações do usuario e a sua criação
        form = UserForm(request.POST)
        v_form = VendorForm(request.POST, request.FILES)
        if form.is_valid() and v_form.is_valid:
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
            user.role = User.VENDOR
            user.save()
            vendor = v_form.save(commit=False)
            vendor.user = user
            vendor_name = v_form.cleaned_data['vendor_name']
            vendor.vendor_slug = slugify(vendor_name)+'-'+str(user.id)
            user_profile = UserProfile.objects.get(user=user)
            vendor.user_profile = user_profile
            vendor.save()

            send_verification_email(request, user)
            messages.success(request, 'Sua conta foi criado com sucesso, por gentileza, aguardar a aprovação do seu cadastro.')
            return redirect('registerVendor')
        else:
            print('formulario invalido')
            print(form.errors)
    else:
        form = UserForm()
        v_form = VendorForm()

    context = {
        'form': form,
        'v_form': v_form,
    }
    return render(request, 'accounts/registerVendor.html', context)

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Parabéns! A sua conta foi ativada com sucesso!')
        return redirect('myAccount')
    else:
        messages.error(request, 'Link de ativação inválido.')
        return redirect('myAccount')

def login(request):
    if request.user.is_authenticated:
        messages.warning(request, 'Você já está logado!')
        return redirect('myAccount')
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)
        if user is not None:
            auth.login(request, user)
            messages.success(request, 'Usuário logado com sucesso!')
            return redirect('myAccount')
        else:
            messages.error(request, 'Usuário ou senha inválida.')        
            return redirect('login')
    return render(request, 'accounts/login.html')

def logout(request):
    auth.logout(request)
    messages.info(request, 'Sessão finalizada com êxito.')
    return redirect('login')

@login_required(login_url='login')
def myAccount(request):
    user = request.user
    redirectUrl = detectUser(user)
    return redirect(redirectUrl)

@login_required(login_url='login')
@user_passes_test(check_role_customer)
def custDashboard(request):
    return render(request, 'accounts/custDashboard.html')

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    return render(request, 'accounts/vendorDashboard.html')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact=email)
            #enviar o email para resetar a senha
            send_password_reset_email(request, user)

            messages.success(request, 'O link com alteração de senha, foi enviado para o seu email.')
            return redirect('login')
        else:
            messages.error(request, 'Favor verificar a conta informada, não foi encontrada.')
            return redirect('forgot_password')
    return render(request, 'accounts/forgot_password.html')

def reset_password_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None 

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.info(request, 'Por favor, insira a sua nova senha.')
        return redirect('reset_password')
    else:
        messages.error(request, 'Este link expirou.')
        return redirect('myAccount')

def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['password']
        
        if password == confirm_password:
            pk = request.session.get('uid')
            user = User.objects.get(pk=pk)
            user.set_password(password)
            user.is_active = True
            user.save()
            messages.success(request, 'A sua senha foi alterada com sucesso.')
            return redirect('login')
        else:
            messages.error(request, 'As senhas não conferem.')
            return redirect('reset_password')
    return render(request, 'accounts/reset_password.html')

