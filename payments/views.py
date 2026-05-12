from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging

from .models import MpesaTransaction
from .mpesa import initiate_stk_push, query_stk_status
from orders.models import Order, OrderStatusHistory

logger = logging.getLogger(__name__)


@require_POST
def initiate_mpesa(request):
    """Start STK Push for an order."""
    data = json.loads(request.body)
    phone = data.get('phone', '')
    order_id = data.get('order_id') or request.session.get('pending_order_id')
    
    if not phone or not order_id:
        return JsonResponse({'success': False, 'error': 'Phone and order required'}, status=400)
    
    order = get_object_or_404(Order, id=order_id)
    
    result = initiate_stk_push(
        phone_number=phone,
        amount=float(order.total),
        order_number=order.order_number,
    )
    
    if result['success']:
        MpesaTransaction.objects.create(
            order=order,
            merchant_request_id=result.get('merchant_request_id', ''),
            checkout_request_id=result['checkout_request_id'],
            phone_number=phone,
            amount=order.total,
            status='pending',
        )
        return JsonResponse({
            'success': True,
            'checkout_request_id': result['checkout_request_id'],
            'message': result.get('customer_message', 'Check your phone for M-Pesa prompt.'),
            'order_number': order.order_number,
        })
    else:
        return JsonResponse({'success': False, 'error': result.get('error', 'Payment failed')}, status=400)


@require_POST
def check_payment_status(request):
    """Poll payment status."""
    data = json.loads(request.body)
    checkout_request_id = data.get('checkout_request_id')
    
    if not checkout_request_id:
        return JsonResponse({'success': False, 'error': 'No checkout ID'}, status=400)
    
    try:
        txn = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
    except MpesaTransaction.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Transaction not found'}, status=404)
    
    if txn.status == 'success':
        return JsonResponse({
            'success': True,
            'status': 'success',
            'order_number': txn.order.order_number if txn.order else '',
            'receipt': txn.mpesa_receipt_number,
        })
    
    # Query M-Pesa
    result = query_stk_status(checkout_request_id)
    result_code = result.get('ResultCode')
    
    if result_code == 0:
        txn.status = 'success'
        txn.result_code = 0
        txn.save()
        if txn.order:
            txn.order.payment_status = 'paid'
            txn.order.status = 'confirmed'
            txn.order.save()
            OrderStatusHistory.objects.create(
                order=txn.order, status='confirmed',
                note='Payment received via M-Pesa.'
            )
        return JsonResponse({'success': True, 'status': 'success', 'order_number': txn.order.order_number if txn.order else ''})
    
    elif result_code == 1032:
        txn.status = 'cancelled'
        txn.result_desc = 'User cancelled'
        txn.save()
        return JsonResponse({'success': False, 'status': 'cancelled', 'error': 'Payment was cancelled.'})
    
    return JsonResponse({'success': False, 'status': 'pending', 'message': 'Waiting for payment...'})


@csrf_exempt
def mpesa_callback(request):
    """M-Pesa callback endpoint."""
    if request.method != 'POST':
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'OK'})
    
    try:
        data = json.loads(request.body)
        callback = data.get('Body', {}).get('stkCallback', {})
        
        checkout_request_id = callback.get('CheckoutRequestID')
        merchant_request_id = callback.get('MerchantRequestID')
        result_code = callback.get('ResultCode')
        result_desc = callback.get('ResultDesc', '')
        
        try:
            txn = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
        except MpesaTransaction.DoesNotExist:
            logger.warning(f"M-Pesa callback for unknown transaction: {checkout_request_id}")
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
        
        txn.result_code = result_code
        txn.result_desc = result_desc
        
        if result_code == 0:
            # Payment successful
            callback_metadata = callback.get('CallbackMetadata', {}).get('Item', [])
            receipt = ''
            for item in callback_metadata:
                if item.get('Name') == 'MpesaReceiptNumber':
                    receipt = item.get('Value', '')
            
            txn.status = 'success'
            txn.mpesa_receipt_number = receipt
            txn.save()
            
            if txn.order:
                txn.order.payment_status = 'paid'
                txn.order.mpesa_receipt = receipt
                txn.order.status = 'confirmed'
                txn.order.save()
                OrderStatusHistory.objects.create(
                    order=txn.order, status='confirmed',
                    note=f'M-Pesa payment confirmed. Receipt: {receipt}'
                )
        else:
            txn.status = 'failed'
            txn.save()
        
        logger.info(f"M-Pesa callback processed: {checkout_request_id} - Code {result_code}")
    
    except Exception as e:
        logger.error(f"M-Pesa callback error: {e}")
    
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
