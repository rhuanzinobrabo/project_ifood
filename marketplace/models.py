"""
Arquivo: marketplace/models.py
Descrição: Contém todos os modelos de dados do marketplace, incluindo:
- Carrinho de compras (Cart)
- Favoritos de restaurantes (FavoriteRestaurant)
- Pedidos e itens de pedido (Order, OrderItem)
- Pagamentos (Payment)
- Notas fiscais (Invoice)
- Taxas (Tax)

Dependências principais:
- accounts/models.py: Modelos de usuário e endereço
- menu/models.py: Modelos de itens de comida
- vendor/models.py: Modelos de restaurantes
"""

# Imports do Django
from django.db import models
from django.utils import timezone

# Imports locais (do próprio projeto)
from accounts.models import User, UserAddress
from menu.models import FoodItem
from vendor.models import Vendor

class Cart(models.Model):
    """
    Modelo para armazenar itens no carrinho de compras do usuário.
    
    Cada registro representa um item específico no carrinho de um usuário,
    com sua respectiva quantidade. O carrinho é temporário e existe apenas
    até que o pedido seja finalizado.
    
    Relacionamentos:
    - Pertence a um User (muitos para um)
    - Referencia um FoodItem (muitos para um)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuário proprietário do carrinho")
    fooditem = models.ForeignKey(FoodItem, on_delete=models.CASCADE, help_text="Item de comida adicionado ao carrinho")
    quantity = models.PositiveIntegerField(help_text="Quantidade do item no carrinho")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Data e hora de criação do registro")
    updated_at = models.DateTimeField(auto_now=True, help_text="Data e hora da última atualização")

    def __str__(self):
        return f"{self.user.email} - {self.fooditem.food_title} - {self.quantity}"


class FavoriteRestaurant(models.Model):
    """
    Modelo para armazenar restaurantes favoritos dos usuários.
    
    Permite que usuários marquem restaurantes como favoritos para
    acesso rápido e filtragem. Cada combinação usuário-restaurante
    é única, garantindo que um restaurante não seja favoritado
    múltiplas vezes pelo mesmo usuário.
    
    Relacionamentos:
    - Pertence a um User (muitos para um)
    - Referencia um Vendor/restaurante (muitos para um)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuário que favoritou o restaurante")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, help_text="Restaurante favoritado")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Data e hora em que o restaurante foi favoritado")

    class Meta:
        unique_together = ('user', 'vendor')
        verbose_name = 'Restaurante Favorito'
        verbose_name_plural = 'Restaurantes Favoritos'

    def __str__(self):
        return f"{self.user.email} - {self.vendor.vendor_name}"


class Tax(models.Model):
    """
    Modelo para armazenar tipos de taxas aplicáveis aos pedidos.
    
    Permite configurar diferentes tipos de taxas (como entrega, serviço, etc.)
    com suas respectivas porcentagens. Taxas podem ser ativadas ou desativadas
    conforme necessário.
    """
    tax_type = models.CharField(max_length=20, unique=True, help_text="Tipo de taxa (ex: Entrega, Serviço)")
    tax_percentage = models.DecimalField(decimal_places=2, max_digits=4, verbose_name='Taxa (%)', 
                                        help_text="Porcentagem da taxa a ser aplicada sobre o subtotal")
    is_active = models.BooleanField(default=True, help_text="Indica se a taxa está ativa e deve ser aplicada aos pedidos")

    class Meta:
        verbose_name_plural = 'Taxas'

    def __str__(self):
        return self.tax_type


class Order(models.Model):
    """
    Modelo principal para armazenar pedidos dos usuários.
    
    Contém todas as informações relacionadas a um pedido, incluindo
    dados do cliente, endereço de entrega, valores, status e informações
    de pagamento. Um pedido pode conter itens de múltiplos restaurantes.
    
    Relacionamentos:
    - Pertence a um User (muitos para um)
    - Associado a um UserAddress (muitos para um)
    - Pode envolver múltiplos Vendors/restaurantes (muitos para muitos)
    - Possui múltiplos OrderItems (um para muitos)
    - Pode ter múltiplos Payments (um para muitos)
    - Pode ter uma Invoice (um para um)
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('CONFIRMED', 'Confirmado'),
        ('PREPARING', 'Em Preparo'),
        ('READY', 'Pronto'),
        ('ON_THE_WAY', 'Em Entrega'),
        ('DELIVERED', 'Entregue'),
        ('CANCELLED', 'Cancelado'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('PAID', 'Pago'),
        ('FAILED', 'Falhou'),
        ('REFUNDED', 'Reembolsado'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuário que realizou o pedido")
    address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True, blank=True, 
                               help_text="Endereço de entrega selecionado")
    vendors = models.ManyToManyField(Vendor, blank=True, help_text="Restaurantes envolvidos no pedido")
    order_number = models.CharField(max_length=20, help_text="Número único do pedido")
    first_name = models.CharField(max_length=50, help_text="Nome do cliente")
    last_name = models.CharField(max_length=50, help_text="Sobrenome do cliente")
    phone = models.CharField(max_length=15, blank=True, help_text="Telefone de contato")
    email = models.EmailField(max_length=50, help_text="Email de contato")
    address_line_1 = models.CharField(max_length=50, help_text="Primeira linha do endereço de entrega")
    address_line_2 = models.CharField(max_length=50, blank=True, help_text="Segunda linha do endereço de entrega (opcional)")
    country = models.CharField(max_length=15, blank=True, help_text="País")
    state = models.CharField(max_length=15, blank=True, help_text="Estado")
    city = models.CharField(max_length=50, help_text="Cidade")
    postal_code = models.CharField(max_length=10, help_text="CEP")
    order_note = models.CharField(max_length=500, blank=True, help_text="Observações adicionais sobre o pedido")
    order_total = models.FloatField(help_text="Valor total do pedido incluindo taxas")
    tax = models.FloatField(help_text="Valor total das taxas aplicadas")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING', 
                             help_text="Status atual do pedido")
    payment_status = models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default='PENDING', 
                                     help_text="Status do pagamento")
    is_ordered = models.BooleanField(default=False, help_text="Indica se o pedido foi confirmado")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Data e hora de criação do pedido")
    updated_at = models.DateTimeField(auto_now=True, help_text="Data e hora da última atualização")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def generate_order_number(self):
        """
        Gera um número único para o pedido baseado na data e ID.
        
        Retorna:
            str: Número do pedido no formato AAAAMMDD + ID com zeros à esquerda
        """
        yr = int(timezone.now().strftime('%Y'))
        mt = int(timezone.now().strftime('%m'))
        dt = int(timezone.now().strftime('%d'))
        d = timezone.now().strftime('%Y%m%d')
        order_number = d + str(self.id).zfill(5)
        return order_number


class OrderItem(models.Model):
    """
    Modelo para armazenar itens individuais de um pedido.
    
    Cada registro representa um item específico dentro de um pedido,
    com sua quantidade, preço unitário e valor total. Os dados do item
    são copiados do FoodItem no momento da criação para preservar o
    histórico mesmo se o item original for alterado ou excluído.
    
    Relacionamentos:
    - Pertence a um Order (muitos para um)
    - Referencia um FoodItem (muitos para um)
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', 
                             help_text="Pedido ao qual este item pertence")
    fooditem = models.ForeignKey(FoodItem, on_delete=models.CASCADE, 
                                help_text="Item de comida pedido")
    quantity = models.IntegerField(help_text="Quantidade do item")
    price = models.FloatField(help_text="Preço unitário do item no momento do pedido")
    amount = models.FloatField(help_text="Valor total (preço × quantidade)")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Data e hora de criação")
    updated_at = models.DateTimeField(auto_now=True, help_text="Data e hora da última atualização")

    def __str__(self):
        return self.fooditem.food_title


class Payment(models.Model):
    """
    Modelo para armazenar informações de pagamento dos pedidos.
    
    Registra detalhes sobre o pagamento de um pedido, incluindo
    método utilizado, valor pago e status. Um pedido pode ter
    múltiplos registros de pagamento em caso de tentativas
    repetidas ou reembolsos.
    
    Relacionamentos:
    - Pertence a um User (muitos para um)
    - Associado a um Order (muitos para um)
    """
    PAYMENT_METHOD_CHOICES = (
        ('CREDIT_CARD', 'Cartão de Crédito'),
        ('DEBIT_CARD', 'Cartão de Débito'),
        ('PIX', 'PIX'),
        ('CASH', 'Dinheiro'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('PAID', 'Pago'),
        ('FAILED', 'Falhou'),
        ('REFUNDED', 'Reembolsado'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuário que realizou o pagamento")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', 
                             help_text="Pedido associado ao pagamento")
    payment_id = models.CharField(max_length=100, help_text="Identificador único do pagamento")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, 
                                     help_text="Método de pagamento utilizado")
    amount_paid = models.FloatField(help_text="Valor pago")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, help_text="Status do pagamento")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Data e hora do pagamento")

    def __str__(self):
        return self.payment_id


class Invoice(models.Model):
    """
    Modelo para armazenar notas fiscais dos pedidos.
    
    Cada pedido pode ter uma nota fiscal associada, que é gerada
    após a confirmação do pagamento. A nota fiscal contém um número
    único e pode ter um arquivo PDF associado.
    
    Relacionamentos:
    - Associada a um Order (um para um)
    """
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice', 
                                help_text="Pedido associado à nota fiscal")
    invoice_number = models.CharField(max_length=20, unique=True, help_text="Número único da nota fiscal")
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True, 
                               help_text="Arquivo PDF da nota fiscal")
    invoice_date = models.DateTimeField(auto_now_add=True, help_text="Data e hora de emissão da nota fiscal")
    
    def __str__(self):
        return self.invoice_number
    
    def generate_invoice_number(self):
        """
        Gera um número único para a nota fiscal baseado na data e ID.
        
        Retorna:
            str: Número da nota fiscal no formato NF-AAAAMMDD + ID com zeros à esquerda
        """
        yr = int(timezone.now().strftime('%Y'))
        mt = int(timezone.now().strftime('%m'))
        dt = int(timezone.now().strftime('%d'))
        d = timezone.now().strftime('%Y%m%d')
        invoice_number = 'NF-' + d + str(self.id).zfill(5)
        return invoice_number
