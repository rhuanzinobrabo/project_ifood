from pathlib import Path
from django.contrib.messages import constants as messages
import ssl
import urllib.request

# ========================
# Caminhos e segurança
# ========================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-6edyx5#lb@3!q7ztph^xteofa0x#mv6s^we2-96i)eem%s=lbn'  # ⚠️ Use variáveis de ambiente em produção
DEBUG = True
ALLOWED_HOSTS = []

# ========================
# Login e Redirecionamento
# ========================
LOGIN_URL = '/conta/request-otp/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ========================
# Apps Instalados
# ========================
INSTALLED_APPS = [
    # Django padrão
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps do projeto
    'accounts.apps.AccountsConfig',  # ✅ Importa signals automaticamente
    'vendor',
    'menu',
    'marketplace',

    # Terceiros
    'social_django',
]

# ========================
# Middlewares
# ========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ========================
# URL e WSGI
# ========================
ROOT_URLCONF = 'ifood_main.urls'
WSGI_APPLICATION = 'ifood_main.wsgi.application'

# ========================
# Templates
# ========================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Personalizados
                'accounts.context_processors.get_vendor',

                # Social Auth
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]


# ========================
# Banco de Dados
# ========================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'foodOnline_db',
        'USER': 'postgres',
        'PASSWORD': 'toor',
        'HOST': 'localhost',
    }
}

# ========================
# Usuário customizado
# ========================
AUTH_USER_MODEL = 'accounts.User'

# ========================
# Backends de Autenticação
# ========================
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

# ========================
# Validações de Senha
# ========================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ========================
# Internacionalização
# ========================
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ========================
# Arquivos estáticos e mídia
# ========================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = ['ifood_main/static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ========================
# E-mail
# ========================
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = '587'
EMAIL_HOST_USER = 'rhuanalves117@gmail.com'
EMAIL_HOST_PASSWORD = 'uxkv hywt zgpz hjvg'  
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'Projeto - Ifood'

# ========================
# Social Auth (Google)
# ========================
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '25374504230-ctd41a83bmviqljrcg2eupq9aaumgmun.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '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'

# ========================
# Outras Configurações
# ========================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# ========================
# Desativa verificação de certificado SSL (local)
# ========================
ssl._create_default_https_context = ssl._create_unverified_context
