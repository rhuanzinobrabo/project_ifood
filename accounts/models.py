from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta

# -------------------------
# Custom User Manager
# -------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, username=None, first_name=None, last_name=None, password=None, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório.')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username or self.generate_username(email),
            first_name=first_name or '',
            last_name=last_name or '',
            **extra_fields
        )
        user.set_password(password)
        user.is_active = True  # Ativo por padrão (para login via OTP ou OAuth)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not password:
            raise ValueError('Superusuários precisam de senha.')

        return self.create_user(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields
        )

    def generate_username(self, email):
        base_username = email.split('@')[0]
        # Garante que não repita
        username = base_username
        counter = 1
        while self.model.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        return username

# -------------------------
# Custom User Model
# -------------------------
class User(AbstractBaseUser, PermissionsMixin):
    RESTAURANT = 1
    CUSTOMER = 2

    ROLE_CHOICES = (
        (RESTAURANT, 'Restaurante'),
        (CUSTOMER, 'Cliente'),
    )

    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    username = models.CharField(max_length=50, unique=True, blank=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, null=True, blank=True)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email

    def get_role(self):
        if self.role == self.RESTAURANT:
            return "Restaurante"
        elif self.role == self.CUSTOMER:
            return "Cliente"
        return ""

# -------------------------
# User Profile Model
# -------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='users/profile_pictures/', blank=True, null=True)
    cover_photo = models.ImageField(upload_to='users/cover_photos/', blank=True, null=True)
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    pin_code = models.CharField(max_length=10, blank=True, null=True)
    latitude = models.CharField(max_length=20, blank=True, null=True)
    longitude = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)

# -------------------------
# OTP Authentication Model
# -------------------------
class OTPModel(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.PositiveIntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def is_blocked(self):
        return self.blocked_until and timezone.now() < self.blocked_until

    def __str__(self):
        return f"OTP para {self.email} - {self.otp}"

class UserAddress(models.Model):
    """
    Endereços de usuário para entrega e faturamento.
    
    Permite que um usuário tenha múltiplos endereços cadastrados,
    com diferentes tipos (casa, trabalho, etc.) e a possibilidade
    de definir um endereço como padrão.
    
    Relacionamentos:
    - Pertence a um User (muitos para um)
    """
    ADDRESS_TYPE_CHOICES = (
        ("HOME", "Casa"),
        ("WORK", "Trabalho"),
        ("OTHER", "Outro"),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses",
                            help_text="Usuário proprietário deste endereço")
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default="HOME",
                                   help_text="Tipo de endereço (Casa, Trabalho, Outro)")
    address_line1 = models.CharField(max_length=100,
                                    help_text="Primeira linha do endereço (rua, número)")
    address_line2 = models.CharField(max_length=100, blank=True, default="",
                                    help_text="Segunda linha do endereço (complemento)")
    city = models.CharField(max_length=50,
                           help_text="Cidade")
    state = models.CharField(max_length=50,
                            help_text="Estado")
    country = models.CharField(max_length=50, default="Brasil",
                              help_text="País")
    postal_code = models.CharField(max_length=10,
                                  help_text="CEP")
    latitude = models.DecimalField(max_digits=18, decimal_places=15, blank=True, null=True,
                                  help_text="Latitude da localização")
    longitude = models.DecimalField(max_digits=18, decimal_places=15, blank=True, null=True,
                                   help_text="Longitude da localização")
    is_default = models.BooleanField(default=False,
                                    help_text="Indica se este é o endereço padrão do usuário")
    created_at = models.DateTimeField(auto_now_add=True,
                                     help_text="Data de criação do endereço")
    updated_at = models.DateTimeField(auto_now=True,
                                     help_text="Data da última atualização do endereço")

    def __str__(self):
        return f"{self.address_type} - {self.address_line1}, {self.city}"
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir que apenas um endereço seja definido como padrão.
        
        Se este endereço for definido como padrão, remove o status padrão de outros endereços.
        Se este for o primeiro endereço do usuário, define-o automaticamente como padrão.
        """
        # Se este endereço for definido como padrão, remova o status padrão de outros endereços
        if self.is_default:
            UserAddress.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        
        # Se este for o primeiro endereço do usuário, defina-o como padrão
        if not self.pk and not UserAddress.objects.filter(user=self.user).exists():
            self.is_default = True
            
        super(UserAddress, self).save(*args, **kwargs)