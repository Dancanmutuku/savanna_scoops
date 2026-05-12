from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderStatusInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'total', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'mpesa_receipt']
    inlines = [OrderItemInline, OrderStatusInline]
