from django.contrib import admin
from .models import InventoryItem, StockMovement, AuditLog

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'current_stock', 'min_stock', 'unit']
    list_editable = ['current_stock']
    list_filter = ['category', 'is_active']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['actor_name', 'action', 'severity', 'created_at']
    list_filter = ['severity', 'module']
