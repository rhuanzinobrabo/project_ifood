from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User, UserProfile
from social_django.models import UserSocialAuth
from django.utils.text import slugify


@receiver(post_save, sender=User)
def create_user_profile_if_complete(sender, instance, created, **kwargs):
    """
    Cria o perfil do usuário somente se o cadastro estiver completo (nome e role definidos).
    """
    if created:
        if instance.first_name and instance.role:
            UserProfile.objects.get_or_create(user=instance)
            print(f"[✓] Perfil criado para {instance.email}")
        else:
            print(f"[!] Usuário {instance.email} criado sem perfil (aguardando cadastro completo)")
    else:
        # Garante que o perfil sempre exista após edição de usuário
        if instance.first_name and instance.role:
            UserProfile.objects.get_or_create(user=instance)


@receiver(pre_save, sender=User)
def log_user_pre_save(sender, instance, **kwargs):
    """
    Apenas loga que o usuário está sendo salvo (útil para debug).
    """
    print(f"📝 Salvando usuário: {instance.email}")


@receiver(post_save, sender=UserSocialAuth)
def complete_user_from_google(sender, instance, created, **kwargs):
    """
    Preenche nome e username do usuário após login com Google, se ainda estiverem faltando.
    """
    user = instance.user
    data = instance.extra_data

    changed = False

    if not user.first_name and data.get('given_name'):
        user.first_name = data['given_name']
        changed = True

    if not user.last_name and data.get('family_name'):
        user.last_name = data['family_name']
        changed = True

    if not user.username:
        base = slugify(user.first_name or "user")
        count = User.objects.filter(username__startswith=base).count()
        user.username = f"{base}{count+1}" if count else base
        changed = True

    if changed:
        user.save()
        print(f"[✓] Dados completados do Google para {user.email}")
