from django.urls import path
from . import views

urlpatterns = [
    path('mpesa/initiate/', views.initiate_mpesa, name='initiate_mpesa'),
    path('mpesa/status/', views.check_payment_status, name='check_payment_status'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('manual/complete/', views.complete_manual_payment, name='complete_manual_payment'),
]
