# ifood_main/urls.py

from django.contrib import admin
from django.urls import path, include
from . import views # Mantém a importação se houver views em ifood_main
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("conta/", include("accounts.urls")), # Mantém prefixo /conta/
    path("oauth/", include("social_django.urls", namespace="social")), # Mantém prefixo /oauth/
    path("mercado/", include("marketplace.urls")), # Mantém prefixo /mercado/
    
    # ADICIONADO: Inclui as URLs do app menu
    path("menu/", include("menu.urls")), 

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Adiciona a configuração para arquivos estáticos em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

