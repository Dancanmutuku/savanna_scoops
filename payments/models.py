from django.db import models
from orders.models import Order


class MpesaTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='mpesa_transactions', 
        null=True, 
        blank=True
    )
    merchant_request_id = models.CharField(max_length=100, blank=True)
    # unique=True automatically creates a unique index on checkout_request_id
    checkout_request_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Added db_index=True for status filtering (e.g., pending vs success queries)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending', 
        db_index=True
    )
    # Added db_index=True for fast lookups by M-Pesa receipt code
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, db_index=True)
    
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Composite index for filtering transactions by status sorted by recent date
            models.Index(fields=['status', '-created_at'], name='mpesa_status_created_idx'),
        ]

    def __str__(self):
        return f"STK {self.checkout_request_id} - {self.status}"