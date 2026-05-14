from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('inventory/', views.inventory_list, name='admin_inventory'),
    path('inventory/update/<int:item_id>/', views.inventory_update, name='inventory_update'),
    path('orders/', views.orders_admin, name='admin_orders'),
    path('orders/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('orders/<int:order_id>/invoice/', views.invoice_view, name='admin_invoice'),
    path('analytics/', views.analytics_view, name='admin_analytics'),
    path('audit/', views.audit_view, name='admin_audit'),
    path('system-logs/', views.system_logs_view, name='admin_system_logs'),
    path('flavors/', views.flavors_admin, name='admin_flavors'),
    path('models/', views.admin_models_view, name='admin_models'),
    path('models/<str:app_label>/<str:model_name>/', views.admin_model_list, name='admin_model_list'),
    path('models/<str:app_label>/<str:model_name>/add/', views.admin_model_form, name='admin_model_add'),
    path('models/<str:app_label>/<str:model_name>/<int:object_id>/edit/', views.admin_model_form, name='admin_model_edit'),
    path('models/<str:app_label>/<str:model_name>/<int:object_id>/delete/', views.admin_model_delete, name='admin_model_delete'),
]
