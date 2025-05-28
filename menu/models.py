"""
Arquivo: menu/models.py
Descrição: Contém os modelos relacionados ao cardápio dos restaurantes, incluindo:
- Categorias de alimentos (Category)
- Itens de comida (FoodItem) com suas propriedades e disponibilidade

Dependências principais:
- vendor/models.py: Modelo de restaurante (Vendor) ao qual os itens estão vinculados
"""

# Imports do Django
from django.db import models

# Imports locais (do próprio projeto)
from vendor.models import Vendor

class Category(models.Model):
    """
    Modelo para categorias de alimentos no cardápio de um restaurante.
    
    Cada restaurante pode ter múltiplas categorias para organizar seus
    itens de comida (ex: Entradas, Pratos Principais, Sobremesas, etc.).
    
    Relacionamentos:
    - Pertence a um Vendor/restaurante (muitos para um)
    - Pode ter múltiplos FoodItems (um para muitos)
    """
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, 
                              help_text="Restaurante ao qual esta categoria pertence")
    category_name = models.CharField(max_length=50, unique=True, 
                                    help_text="Nome da categoria (ex: Entradas, Sobremesas)")
    slug = models.SlugField(max_length=100, unique=True, 
                           help_text="Slug para URL (gerado a partir do nome da categoria)")
    description = models.TextField(max_length=250, blank=True, 
                                  help_text="Descrição opcional da categoria")
    create_at = models.DateTimeField(auto_now_add=True, 
                                    help_text="Data e hora de criação da categoria")
    updated_at = models.DateTimeField(auto_now=True, 
                                     help_text="Data e hora da última atualização")

    class Meta:
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'
        ordering = ('category_name',)

    def clean(self):
        """
        Garante que o nome da categoria comece com letra maiúscula.
        """
        self.category_name = self.category_name.capitalize()

    def __str__(self):
        return self.category_name


class FoodItem(models.Model):
    """
    Modelo para itens de comida no cardápio de um restaurante.
    
    Representa um prato ou item específico que pode ser pedido,
    com detalhes como preço, descrição e imagem. Cada item pertence
    a uma categoria específica dentro do cardápio de um restaurante.
    
    Relacionamentos:
    - Pertence a um Vendor/restaurante (muitos para um)
    - Pertence a uma Category (muitos para um)
    - Pode estar em múltiplos Cart (um para muitos)
    - Pode estar em múltiplos OrderItem (um para muitos)
    """
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, 
                              help_text="Restaurante ao qual este item pertence")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='fooditems', 
                                help_text="Categoria à qual este item pertence")
    food_title = models.CharField(max_length=50, 
                                 help_text="Nome do item de comida")
    slug = models.SlugField(max_length=100, unique=True, 
                           help_text="Slug para URL (gerado a partir do nome do item)")
    description = models.TextField(max_length=250, blank=True, 
                                  help_text="Descrição do item de comida")
    price = models.DecimalField(max_digits=10, decimal_places=2, 
                               help_text="Preço do item")
    image = models.ImageField(upload_to='foodimages', 
                             help_text="Imagem do item de comida")
    is_available = models.BooleanField(default=True, 
                                      help_text="Indica se o item está disponível para pedido")
    created_at = models.DateTimeField(auto_now_add=True, 
                                     help_text="Data e hora de criação do item")
    updated_at = models.DateTimeField(auto_now=True, 
                                     help_text="Data e hora da última atualização")

    class Meta:
        verbose_name = 'item de comida'
        verbose_name_plural = 'itens de comida'
        ordering = ('created_at',)

    def __str__(self):
        return self.food_title
