from django.db import models
from django.contrib.auth.models import User
from store.models import Flavor
import uuid


def generate_order_number():
    return f"SS-{uuid.uuid4().hex[:8].upper()}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True, default=generate_order_number)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    delivery_address = models.TextField()
    delivery_instructions = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=150)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, default='M-Pesa')
    payment_status = models.CharField(max_length=20, default='pending')
    mpesa_receipt = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number} - {self.customer_name}"

    @property
    def status_percentage(self):
        stages = ['pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered']
        try:
            idx = stages.index(self.status)
            return int(((idx + 1) / len(stages)) * 100)
        except ValueError:
            return 0

    @property
    def status_display_color(self):
        colors = {
            'pending': 'yellow',
            'confirmed': 'blue',
            'preparing': 'orange',
            'out_for_delivery': 'purple',
            'delivered': 'green',
            'cancelled': 'red',
        }
        return colors.get(self.status, 'gray')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    flavor = models.ForeignKey(Flavor, on_delete=models.SET_NULL, null=True)
    flavor_name = models.CharField(max_length=200)  # Snapshot
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.flavor_name}"

    def save(self, *args, **kwargs):
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=30)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['created_at']
