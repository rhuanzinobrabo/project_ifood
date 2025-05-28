from django.db import models
from django.utils import timezone
from accounts.models import User, UserAddress
from menu.models import FoodItem
from vendor.models import Vendor

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fooditem = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.user
    
    @property
    def item_total(self):
        """Calcula o total para este item do carrinho"""
        return self.fooditem.price * self.quantity


class Tax(models.Model):
    tax_type = models.CharField(max_length=20, unique=True)
    tax_percentage = models.DecimalField(decimal_places=2, max_digits=4, verbose_name='Tax Percentage (%)')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'tax'

    def __str__(self):
        return self.tax_type


class FavoriteRestaurant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_restaurants')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'vendor')  # Evita duplicatas
        verbose_name = 'Restaurante Favorito'
        verbose_name_plural = 'Restaurantes Favoritos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.first_name} favoritou {self.vendor.vendor_name}"


# Novos modelos para o fluxo de pedido

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('CONFIRMED', 'Confirmado'),
        ('PREPARING', 'Em Preparo'),
        ('READY', 'Pronto para Entrega'),
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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True, blank=True)
    vendors = models.ManyToManyField(Vendor, blank=True)
    order_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)
    order_note = models.CharField(max_length=100, blank=True)
    order_total = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.order_number
    
    def get_total_by_vendor(self):
        """Retorna o total do pedido agrupado por vendor"""
        vendor_totals = {}
        for item in self.orderitem_set.all():
            vendor = item.fooditem.vendor
            if vendor.id in vendor_totals:
                vendor_totals[vendor.id]['subtotal'] += item.amount
            else:
                vendor_totals[vendor.id] = {
                    'vendor': vendor,
                    'subtotal': item.amount
                }
        return vendor_totals
    
    def generate_order_number(self):
        """Gera um número de pedido único baseado na data e ID"""
        yr = int(timezone.now().strftime('%Y'))
        mt = int(timezone.now().strftime('%m'))
        dt = int(timezone.now().strftime('%d'))
        d = timezone.now().strftime('%Y%m%d')
        order_number = d + str(self.id)
        return order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    fooditem = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.fooditem.food_title


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('CREDIT_CARD', 'Cartão de Crédito'),
        ('DEBIT_CARD', 'Cartão de Débito'),
        ('PIX', 'PIX'),
        ('CASH', 'Dinheiro na Entrega'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True, null=True)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CREDIT_CARD')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.payment_id


# Modelo para Nota Fiscal
class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True)
    invoice_date = models.DateTimeField(auto_now_add=True)
    customer_cpf = models.CharField(max_length=14, blank=True, null=True)  # CPF do cliente
    customer_cnpj = models.CharField(max_length=18, blank=True, null=True)  # CNPJ se for pessoa jurídica
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    is_sent = models.BooleanField(default=False)  # Se foi enviada por email
    
    def __str__(self):
        return self.invoice_number
    
    def generate_invoice_number(self):
        """Gera um número de nota fiscal único baseado na data e ID"""
        d = timezone.now().strftime('%Y%m%d')
        invoice_number = f"NF-{d}-{self.id}"
        return invoice_number
