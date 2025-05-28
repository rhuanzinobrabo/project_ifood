"""
Arquivo: vendor/models.py
Descrição: Contém os modelos relacionados aos restaurantes (vendors), incluindo:
- Informações básicas do restaurante (Vendor)
- Configurações de horário de funcionamento
- Status de aprovação e atividade

Dependências principais:
- accounts/models.py: Modelos de usuário (User) e perfil (UserProfile)
- accounts/utils.py: Funções de utilidade para notificações
"""

# Imports do Django
from django.db import models

# Imports locais (do próprio projeto)
from accounts.models import User, UserProfile
from accounts.utils import send_notification


class Vendor(models.Model):
    """
    Modelo principal para restaurantes (vendors) no sistema.
    
    Armazena informações básicas sobre o restaurante, incluindo nome,
    licença e status de aprovação. Cada restaurante está associado a
    um usuário específico com papel de vendedor.
    
    Relacionamentos:
    - Associado a um User (um para um)
    - Associado a um UserProfile (um para um)
    - Pode ter múltiplas Category (um para muitos)
    - Pode ter múltiplos FoodItem (um para muitos)
    - Pode estar em múltiplos Order (muitos para muitos)
    - Pode estar em múltiplos FavoriteRestaurant (um para muitos)
    """
    user = models.OneToOneField(User, related_name='vendor', on_delete=models.CASCADE,
                            help_text="Usuário proprietário do restaurante")
    user_profile = models.OneToOneField(UserProfile, related_name='userprofile', on_delete=models.CASCADE,
                                       help_text="Perfil de usuário associado ao restaurante")
    vendor_name = models.CharField(max_length=50,
                                  help_text="Nome comercial do restaurante")
    vendor_slug = models.SlugField(max_length=100, unique=True,
                                  help_text="Slug para URL (gerado a partir do nome do restaurante)")
    vendor_license = models.ImageField(upload_to='vendor/license',
                                      help_text="Imagem da licença comercial do restaurante")
    is_approved = models.BooleanField(default=False,
                                     help_text="Indica se o restaurante foi aprovado pelo administrador")
    created_at = models.DateTimeField(auto_now_add=True,
                                     help_text="Data e hora de criação do registro")
    modified_at = models.DateTimeField(auto_now=True,
                                      help_text="Data e hora da última modificação")

    def __str__(self):
        return self.vendor_name

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para enviar notificações por email quando
        o status de aprovação do restaurante é alterado.
        
        Quando um restaurante é aprovado ou desaprovado, um email de notificação
        é enviado ao proprietário informando sobre a mudança de status.
        """
        if self.pk is not None:
            # Update
            orig = Vendor.objects.get(pk=self.pk)
            if orig.is_approved != self.is_approved:
                mail_template = 'accounts/emails/admin_approval_email.html'
                context = {
                    'user': self.user,
                    'is_approved': self.is_approved,
                    'to_email': self.user.email,
                }
                if self.is_approved:
                    # Send notification email
                    mail_subject = "Parabéns! Seu restaurante foi aprovado."
                    send_notification(mail_subject, mail_template, context)
                else:
                    # Send notification email
                    mail_subject = "Desculpe! Você não está qualificado para publicar seu menu no nosso marketplace."
                    send_notification(mail_subject, mail_template, context)
        return super(Vendor, self).save(*args, **kwargs)
