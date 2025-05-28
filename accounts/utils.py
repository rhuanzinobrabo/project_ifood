"""
Arquivo: accounts/utils.py
Descrição: Contém funções utilitárias para o app accounts, incluindo:
- Detecção de tipo de usuário para redirecionamento
- Envio de emails para verificação de conta
- Envio de emails para recuperação de senha
- Envio de notificações gerais

Dependências principais:
- Django email system
- accounts/models.py: Modelos User e UserProfile
"""

# Imports da biblioteca padrão Python
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings

def detectUser(user ):
    """
    Detecta o tipo de usuário e retorna a URL de redirecionamento apropriada.
    
    Args:
        user: Instância do modelo User
        
    Returns:
        str: URL para redirecionamento baseada no papel do usuário
    """
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
    """
    Envia email de verificação para ativação de conta.
    
    Args:
        request: Objeto request do Django
        user: Instância do modelo User para quem o email será enviado
    """
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
    """
    Envia email para recuperação de senha.
    
    Args:
        request: Objeto request do Django
        user: Instância do modelo User para quem o email será enviado
    """
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
    """
    Função genérica para envio de notificações por email.
    
    Args:
        mail_subject: Assunto do email
        mail_template: Caminho para o template do email
        context: Dicionário com contexto para renderização do template
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    message = render_to_string(mail_template, context)
    to_email = context['user'].email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.send()
