from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_order, name='create_order'),
    path('confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('status/<str:order_number>/', views.order_status_api, name='order_status_api'),
    path('my-orders/', views.my_orders, name='my_orders'),
]
