from django.contrib import admin
from .models import InventoryItem, StockMovement, AuditLog, SystemLog, UserActivity

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'current_stock', 'min_stock', 'unit']
    list_editable = ['current_stock']
    list_filter = ['category', 'is_active']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['actor_name', 'action', 'severity', 'created_at']
    list_filter = ['severity', 'module']


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'level', 'logger_name', 'message']
    list_filter = ['level', 'logger_name', 'created_at']
    search_fields = ['logger_name', 'message', 'path', 'traceback']
    readonly_fields = ['level', 'logger_name', 'message', 'module', 'function', 'path', 'traceback', 'created_at']


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_key', 'last_seen', 'path', 'ip_address']
    list_filter = ['last_seen', 'user__is_staff']
    search_fields = ['user__username', 'user__email', 'session_key', 'path', 'ip_address']
    readonly_fields = ['user', 'session_key', 'ip_address', 'user_agent', 'path', 'last_seen', 'created_at']
