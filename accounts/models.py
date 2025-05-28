"""
Arquivo: accounts/models.py
Descrição: Contém todos os modelos relacionados a usuários e autenticação, incluindo:
- Usuário personalizado (User) com diferentes papéis (cliente, vendedor, admin)
- Perfil de usuário (UserProfile) com informações adicionais
- Endereços de usuário (UserAddress) para entrega e faturamento
- Funcionalidades de verificação e autenticação

Dependências principais:
- Django auth system: Estende os modelos de autenticação padrão do Django
- signals.py: Contém sinais para criação automática de perfis
"""

# Imports da biblioteca padrão Python
from datetime import timedelta

# Imports do Django
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

# -------------------------
# Custom User Manager
# -------------------------
class UserManager(BaseUserManager):
    """
    Gerenciador personalizado para o modelo de usuário customizado.
    
    Responsável por criar usuários regulares e superusuários com
    os campos obrigatórios e configurações apropriadas para cada tipo.
    """
    def create_user(self, first_name, last_name, username, email, password=None, **extra_fields):
        """
        Cria e salva um usuário regular com os campos fornecidos.
        
        Args:
            first_name (str): Nome do usuário
            last_name (str): Sobrenome do usuário
            username (str): Nome de usuário único
            email (str): Email único do usuário
            password (str, opcional): Senha do usuário
            **extra_fields: Campos adicionais para o modelo de usuário
            
        Returns:
            User: Instância do usuário criado
            
        Raises:
            ValueError: Se email ou username não forem fornecidos
        """
        if not email:
            raise ValueError('Usuário deve ter um endereço de email')
        
        if not username:
            raise ValueError('Usuário deve ter um nome de usuário')
        
        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, first_name, last_name, username, email, password=None, **extra_fields):
        """
        Cria e salva um superusuário com os campos fornecidos.
        
        Args:
            first_name (str): Nome do superusuário
            last_name (str): Sobrenome do superusuário
            username (str): Nome de usuário único
            email (str): Email único do superusuário
            password (str, opcional): Senha do superusuário
            **extra_fields: Campos adicionais para o modelo de usuário
            
        Returns:
            User: Instância do superusuário criado
            
        Raises:
            ValueError: Se is_staff ou is_superuser não forem True
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(first_name, last_name, username, email, password, **extra_fields)


# -------------------------
# Custom User Model
# -------------------------
class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuário personalizado com diferentes papéis e funcionalidades adicionais.
    
    Estende o modelo de usuário padrão do Django para incluir papéis específicos
    (cliente, restaurante, administrador), verificação de email e autenticação OTP.
    
    Relacionamentos:
    - Possui um UserProfile (um para um)
    - Pode ter múltiplos UserAddress (um para muitos)
    """
    VENDOR = 1
    CUSTOMER = 2
    ADMIN = 3
    
    ROLE_CHOICE = (
        (VENDOR, 'Restaurante'),
        (CUSTOMER, 'Cliente'),
        (ADMIN, 'Administrador'),
    )
    
    first_name = models.CharField(max_length=50, help_text="Nome do usuário")
    last_name = models.CharField(max_length=50, help_text="Sobrenome do usuário")
    username = models.CharField(max_length=50, unique=True, help_text="Nome de usuário único")
    email = models.EmailField(max_length=100, unique=True, help_text="Email único do usuário")
    phone_number = models.CharField(max_length=12, blank=True, help_text="Número de telefone do usuário")
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICE, blank=True, null=True, 
                                           help_text="Papel do usuário no sistema")
    
    # Campos obrigatórios
    date_joined = models.DateTimeField(auto_now_add=True, help_text="Data de ingresso no sistema")
    last_login = models.DateTimeField(auto_now_add=True, help_text="Data do último login")
    created_date = models.DateTimeField(auto_now_add=True, help_text="Data de criação do registro")
    modified_date = models.DateTimeField(auto_now=True, help_text="Data da última modificação")
    is_admin = models.BooleanField(default=False, help_text="Indica se o usuário é administrador")
    is_staff = models.BooleanField(default=False, help_text="Indica se o usuário é membro da equipe")
    is_active = models.BooleanField(default=False, help_text="Indica se o usuário está ativo")
    is_superuser = models.BooleanField(default=False, help_text="Indica se o usuário é superusuário")
    
    # Verificação por email
    email_verified = models.BooleanField(default=False, help_text="Indica se o email foi verificado")
    email_verification_token = models.CharField(max_length=100, blank=True, 
                                              help_text="Token para verificação de email")
    
    # Verificação por OTP
    otp = models.CharField(max_length=6, blank=True, help_text="Código OTP para autenticação")
    otp_created_at = models.DateTimeField(null=True, blank=True, help_text="Data de criação do OTP")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        """
        Verifica se o usuário tem uma permissão específica.
        
        Args:
            perm (str): Permissão a ser verificada
            obj (Model, opcional): Objeto específico para verificar permissão
            
        Returns:
            bool: True se o usuário é admin, False caso contrário
        """
        return self.is_admin
    
    def has_module_perms(self, app_label):
        """
        Verifica se o usuário tem permissões para um módulo específico.
        
        Args:
            app_label (str): Rótulo do aplicativo a verificar
            
        Returns:
            bool: True para todos os usuários
        """
        return True
    
    def get_role(self):
        """
        Retorna o nome do papel do usuário em formato legível.
        
        Returns:
            str: Nome do papel (Restaurante, Cliente, Administrador ou Usuário)
        """
        if self.role == 1:
            return 'Restaurante'
        elif self.role == 2:
            return 'Cliente'
        elif self.role == 3:
            return 'Administrador'
        return 'Usuário'
    
    def is_otp_valid(self):
        """
        Verifica se o OTP ainda é válido (10 minutos de validade).
        
        Returns:
            bool: True se o OTP ainda é válido, False caso contrário
        """
        if not self.otp_created_at:
            return False
        
        expiration_time = self.otp_created_at + timedelta(minutes=10)
        return timezone.now() <= expiration_time


# -------------------------
# User Profile Model
# -------------------------
class UserProfile(models.Model):
    """
    Perfil de usuário com informações adicionais.
    
    Armazena informações complementares ao usuário, como fotos de perfil,
    endereço e coordenadas geográficas.
    
    Relacionamentos:
    - Pertence a um User (um para um)
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile',
                               help_text="Usuário associado a este perfil")
    profile_picture = models.ImageField(upload_to='users/profile_pictures', blank=True, null=True,
                                       help_text="Foto de perfil do usuário")
    cover_photo = models.ImageField(upload_to='users/cover_photos', blank=True, null=True,
                                   help_text="Foto de capa do perfil")
    address = models.CharField(max_length=250, blank=True, null=True,
                              help_text="Endereço principal do usuário")
    country = models.CharField(max_length=15, blank=True, null=True,
                              help_text="País do usuário")
    state = models.CharField(max_length=15, blank=True, null=True,
                            help_text="Estado do usuário")
    city = models.CharField(max_length=15, blank=True, null=True,
                           help_text="Cidade do usuário")
    postal_code = models.CharField(max_length=10, blank=True, null=True,
                                  help_text="CEP do usuário")
    latitude = models.CharField(max_length=20, blank=True, null=True,
                               help_text="Latitude da localização do usuário")
    longitude = models.CharField(max_length=20, blank=True, null=True,
                                help_text="Longitude da localização do usuário")
    created_at = models.DateTimeField(auto_now_add=True,
                                     help_text="Data de criação do perfil")
    modified_at = models.DateTimeField(auto_now=True,
                                      help_text="Data da última modificação do perfil")

    def __str__(self):
        return self.user.email
    
    @property
    def full_address(self):
        """
        Retorna o endereço completo formatado.
        
        Combina os componentes do endereço em uma única string formatada.
        
        Returns:
            str: Endereço completo ou mensagem padrão se não houver endereço
        """
        address_parts = []
        if self.address:
            address_parts.append(self.address)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)
        
        return ', '.join(address_parts) if address_parts else 'Endereço não informado'


# -------------------------
# User Address Model
# -------------------------
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
        ('HOME', 'Casa'),
        ('WORK', 'Trabalho'),
        ('OTHER', 'Outro'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses',
                            help_text="Usuário proprietário deste endereço")
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='HOME',
                                   help_text="Tipo de endereço (Casa, Trabalho, Outro)")
    address_line1 = models.CharField(max_length=100,
                                    help_text="Primeira linha do endereço (rua, número)")
    address_line2 = models.CharField(max_length=100, blank=True,
                                    help_text="Segunda linha do endereço (complemento)")
    city = models.CharField(max_length=50,
                           help_text="Cidade")
    state = models.CharField(max_length=50,
                            help_text="Estado")
    country = models.CharField(max_length=50, default='Brasil',
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
            UserAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        
        # Se este for o primeiro endereço do usuário, defina-o como padrão
        if not self.pk and not UserAddress.objects.filter(user=self.user).exists():
            self.is_default = True
            
        super(UserAddress, self).save(*args, **kwargs)
