from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings


def detectUser(user):
    """
    Determina a URL de redirecionamento com base no papel do usuário.
    """
    if user.role == 1:
        redirectUrl = 'vendorDashboard'
        return redirectUrl
    elif user.role == 2:
        redirectUrl = 'custDashboard'
        return redirectUrl
    elif user.role is None and user.is_superadmin:
        redirectUrl = '/admin'
        return redirectUrl


def send_verification_email(request, user):
    """
    Envia e-mail de verificação com link de ativação.
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    mail_subject = 'Ativação da sua conta'
    message = render_to_string('accounts/emails/account_verification_email.html', {
        'user': user,
        'domain': current_site.domain,  # Usa o domínio do site atual
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = 'html'  # Define como HTML
    mail.send()


def send_password_reset_email(request, user):
    """
    Envia e-mail para redefinição de senha com link.
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    mail_subject = 'Alteração da senha de sua conta'
    message = render_to_string('accounts/emails/reset_password_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = 'html'  # Define como HTML
    mail.send()


def send_notification(mail_subject, mail_template, context):
    """
    Envia notificação genérica por e-mail.
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    message = render_to_string(mail_template, context)
    to_email = context['user'].email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = 'html'  # Define como HTML
    mail.send()


def send_otp_email(request, user, mail_subject, email_template, uid=None, token=None):
    """
    Envia e-mail com código OTP e link de ativação para o usuário.
    Usado para autenticação e verificação de conta.

    Args:
        request: Objeto de requisição HTTP.
        user: Objeto do usuário para quem o e-mail será enviado.
        mail_subject: Assunto do e-mail.
        email_template: Caminho do template de e-mail.
        uid: UID codificado em base64 do usuário (opcional).
        token: Token de ativação gerado (opcional).
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    context = {
        'user': user,
        'otp': user.otp,
        'domain': current_site.domain,  # Usa o domínio do site atual
        'uid': uid if uid else urlsafe_base64_encode(force_bytes(user.pk)),
        'token': token if token else default_token_generator.make_token(user),
        'to_email': user.email,
    }
    message = render_to_string(email_template, context)
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = 'html'  # Define como HTML
    mail.send()


def check_role_customer(user):
    """
    Verifica se o usuário tem papel de cliente.
    Usada como decorator para restringir acesso a views específicas.
    """
    if user.role == 2:  # 2 = Cliente
        return True
    return False


def check_role_vendor(user):
    """
    Verifica se o usuário tem papel de restaurante.
    Usada como decorator para restringir acesso a views específicas.
    """
    if user.role == 1:  # 1 = Restaurante
        return True
    return False


def check_role_admin(user):
    """
    Verifica se o usuário é um administrador.
    Usada como decorator para restringir acesso a views administrativas.
    """
    if user.is_superadmin:
        return True
    return False