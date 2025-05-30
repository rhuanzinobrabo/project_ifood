from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings

def detectUser(user):
    if user.role == 1:
        redirectUrl ='vendorDashboard'
        return redirectUrl
    elif user.role == 2:
        redirectUrl = 'custDashboard'
        return redirectUrl
    elif user.role == None and user.is_superadmin:
        redirectUrl = '/admin'
        return redirectUrl
    

def send_verification_email(request, user):
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    mail_subject = 'Ativação da sua conta'
    message = render_to_string('accounts/emails/account_verification_email.html', {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),        
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.send()


def send_password_reset_email(request, user):
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    mail_subject = 'Alteração da senha de sua conta'
    message = render_to_string('accounts/emails/reset_password_email.html', {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),        
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.send()


def send_notification(mail_subject, mail_template, context):
    from_email = settings.DEFAULT_FROM_EMAIL
    message = render_to_string(mail_template, context)
    to_email = context['user'].email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.send()


def send_otp_email(user, mail_subject, email_template):
    """
    Envia email com código OTP para o usuário.
    Usado para autenticação e verificação de conta.
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    context = {
        'user': user,
        'otp': user.otp,
        'to_email': user.email,
    }
    message = render_to_string(email_template, context)
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = "html"
    mail.send()


def check_role_customer(user):
    """
    Verifica se o usuário tem papel de cliente.
    Usada como decorator para restringir acesso a views específicas.
    """
    if user.role == 2:  # 2 = Cliente
        return True
    else:
        return False


def check_role_vendor(user):
    """
    Verifica se o usuário tem papel de restaurante.
    Usada como decorator para restringir acesso a views específicas.
    """
    if user.role == 1:  # 1 = Restaurante
        return True
    else:
        return False


def check_role_admin(user):
    """
    Verifica se o usuário é um administrador.
    Usada como decorator para restringir acesso a views administrativas.
    """
    if user.is_superadmin:
        return True
    else:
        return False
