from django.db import models
from django.contrib.auth.models import User


class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('dairy', 'Dairy'),
        ('sweetener', 'Sweetener'),
        ('flavoring', 'Flavoring'),
        ('packaging', 'Packaging'),
        ('equipment', 'Equipment'),
        ('other', 'Other'),
    ]

    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    max_stock = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    unit = models.CharField(max_length=30, default='Units')
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True, default='Main Storeroom')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def stock_status(self):
        if self.current_stock == 0:
            return 'out'
        elif self.current_stock <= self.min_stock:
            return 'critical'
        elif self.current_stock <= self.min_stock * __import__('decimal').Decimal('1.5'):
            return 'low'
        return 'ok'

    @property
    def stock_percentage(self):
        if self.max_stock == 0:
            return 0
        return min(100, int((float(self.current_stock) / float(self.max_stock)) * 100))


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
        ('waste', 'Waste/Loss'),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    previous_stock = models.DecimalField(max_digits=10, decimal_places=2)
    new_stock = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class AuditLog(models.Model):
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]

    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    actor_name = models.CharField(max_length=200)
    actor_role = models.CharField(max_length=100, blank=True)
    action = models.CharField(max_length=300)
    module = models.CharField(max_length=50, default='General')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    impact = models.CharField(max_length=300, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor_name}: {self.action}"
