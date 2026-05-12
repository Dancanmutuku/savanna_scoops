from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('inventory/', views.inventory_list, name='admin_inventory'),
    path('inventory/update/<int:item_id>/', views.inventory_update, name='inventory_update'),
    path('orders/', views.orders_admin, name='admin_orders'),
    path('orders/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('analytics/', views.analytics_view, name='admin_analytics'),
    path('audit/', views.audit_view, name='admin_audit'),
    path('flavors/', views.flavors_admin, name='admin_flavors'),
]
