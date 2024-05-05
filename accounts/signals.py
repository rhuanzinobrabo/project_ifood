from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User, UserProfile

@receiver(post_save, sender=User)
def post_save_create_profile_receiver(sender, instance, created, **kwargs):
    print(created)
    if created:
        UserProfile.objects.create(user=instance)
        print('o perfil do usuario foi criado.')

    else:
        try:
            profile = UserProfile.objects.get(user=instance)
            profile.save()
        except:
            #criar o perfil do usuario, caso nao exista
            UserProfile.objects.create(user=instance)
            print('perfil nao existe porem foi criado um.')
        print('o usuario foi atualizado')
    

@receiver(pre_save, sender=User)
def pre_save_profile_receiver(sender, instance, **kwargs):
    print(instance.username, 'este usuario está sendo salvo')
# post_save.connect(post_save_create_profile_receiver, sender=User)