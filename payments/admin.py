from django.contrib import admin
from .models import MpesaTransaction

@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ['checkout_request_id', 'phone_number', 'amount', 'status', 'mpesa_receipt_number', 'created_at']
    list_filter = ['status']
    readonly_fields = ['checkout_request_id', 'merchant_request_id', 'result_code', 'result_desc']
