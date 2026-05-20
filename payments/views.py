from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from decimal import Decimal, InvalidOperation
import json
import logging

from .models import MpesaTransaction
from .mpesa import initiate_stk_push, query_stk_status
from orders.models import Order, OrderStatusHistory
from orders.emails import queue_order_confirmation_email

logger = logging.getLogger(__name__)


def _fallback_code(prefix, value):
    suffix = (value or timezone.now().strftime('%Y%m%d%H%M%S'))[-8:].upper()
    return f'{prefix}-{suffix}'


def _result_code_as_int(result_code):
    try:
        return int(result_code)
    except (TypeError, ValueError):
        return None


def _user_can_access_order(user, order):
    return bool(order and (user.is_staff or order.user_id == user.id))


def _callback_metadata_value(callback, name):
    for item in callback.get('CallbackMetadata', {}).get('Item', []):
        if item.get('Name') == name:
            return item.get('Value')
    return None


def _decimal_or_none(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _mark_order_paid(order, method, transaction_code, note=None):
    with transaction.atomic():
        was_paid = order.payment_status == 'paid'
        order.payment_method = method
        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.mpesa_receipt = transaction_code
        order.save()
        OrderStatusHistory.objects.create(
            order=order,
            status='confirmed',
            note=note or f'{method} payment confirmed. Transaction: {transaction_code}',
        )
        if not was_paid:
            cache.delete('analytics:summary')
            logger.info("Order %s marked paid via %s. Receipt: %s", order.order_number, method, transaction_code)
            transaction.on_commit(lambda: queue_order_confirmation_email(order.id))


def _mark_order_cancelled(order, note):
    order.payment_status = 'cancelled'
    order.status = 'cancelled'
    order.save()
    OrderStatusHistory.objects.create(order=order, status='cancelled', note=note)


@require_POST
@login_required
def initiate_mpesa(request):
    """Start STK Push for an order."""
    data = json.loads(request.body)
    phone = data.get('phone', '')
    order_id = data.get('order_id') or request.session.get('pending_order_id')
    
    if not phone or not order_id:
        return JsonResponse({'success': False, 'error': 'Phone and order required'}, status=400)
    
    orders = Order.objects.all() if request.user.is_staff else Order.objects.filter(user=request.user)
    order = get_object_or_404(orders, id=order_id)
    if order.payment_status == 'paid':
        return JsonResponse({'success': False, 'error': 'This order is already paid.'}, status=400)
    
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
@login_required
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

    if txn.order and not _user_can_access_order(request.user, txn.order):
        return JsonResponse({'success': False, 'error': 'Transaction not found'}, status=404)
    
    if txn.status == 'success':
        return JsonResponse({
            'success': True,
            'status': 'success',
            'order_number': txn.order.order_number if txn.order else '',
            'receipt': txn.mpesa_receipt_number,
        })
    
    # Query M-Pesa
    try:
        result = query_stk_status(checkout_request_id)
    except Exception:
        logger.exception("Unexpected M-Pesa status check failure for %s.", checkout_request_id)
        result = {'success': False, 'error': 'Payment status is temporarily unavailable'}

    result_code = _result_code_as_int(result.get('ResultCode'))
    
    if result_code == 0:
        with transaction.atomic():
            txn.status = 'success'
            txn.result_code = 0
            txn.mpesa_receipt_number = txn.mpesa_receipt_number or _fallback_code('MPESA', checkout_request_id)
            txn.save()
            if txn.order:
                _mark_order_paid(
                    txn.order,
                    'M-Pesa',
                    txn.mpesa_receipt_number,
                    f'Payment received via M-Pesa. Receipt: {txn.mpesa_receipt_number}',
                )
        return JsonResponse({
            'success': True,
            'status': 'success',
            'order_number': txn.order.order_number if txn.order else '',
            'receipt': txn.mpesa_receipt_number,
        })
    
    elif result_code == 1032:
        with transaction.atomic():
            txn.status = 'cancelled'
            txn.result_desc = 'User cancelled'
            txn.save()
            if txn.order:
                _mark_order_cancelled(txn.order, 'M-Pesa prompt was cancelled by the customer.')
        return JsonResponse({'success': False, 'status': 'cancelled', 'error': 'Payment has been canceled.'})
    
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
        
        result_code_int = _result_code_as_int(result_code)

        if result_code_int == 0:
            if txn.status == 'success' and txn.order and txn.order.payment_status == 'paid':
                logger.info("Ignoring duplicate M-Pesa success callback for %s.", checkout_request_id)
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})

            receipt = _callback_metadata_value(callback, 'MpesaReceiptNumber')
            receipt = receipt or _fallback_code('MPESA', checkout_request_id)

            paid_amount = _decimal_or_none(_callback_metadata_value(callback, 'Amount'))
            if txn.order and paid_amount is not None and paid_amount != txn.order.total:
                txn.status = 'failed'
                txn.result_code = result_code_int
                txn.result_desc = f'Amount mismatch. Paid {paid_amount}, expected {txn.order.total}.'
                txn.save()
                logger.warning(
                    "Rejected M-Pesa callback for %s due to amount mismatch. Paid: %s Expected: %s",
                    checkout_request_id,
                    paid_amount,
                    txn.order.total,
                )
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
            
            with transaction.atomic():
                txn.status = 'success'
                txn.result_code = result_code_int
                txn.mpesa_receipt_number = receipt
                txn.save()

                if txn.order:
                    _mark_order_paid(txn.order, 'M-Pesa', receipt, f'M-Pesa payment confirmed. Receipt: {receipt}')
        elif result_code_int == 1032:
            with transaction.atomic():
                txn.status = 'cancelled'
                txn.result_code = result_code_int
                txn.save()
                if txn.order:
                    _mark_order_cancelled(txn.order, 'M-Pesa prompt was cancelled by the customer.')
        else:
            txn.status = 'failed'
            txn.save()
        
        logger.info(f"M-Pesa callback processed: {checkout_request_id} - Code {result_code}")
    
    except Exception as e:
        logger.error(f"M-Pesa callback error: {e}")
    
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})


@require_POST
@login_required
def complete_manual_payment(request):
    """Mark an order paid for non-M-Pesa checkout methods."""
    data = json.loads(request.body)
    orders = Order.objects.all() if request.user.is_staff else Order.objects.filter(user=request.user)
    order = get_object_or_404(orders, id=data.get('order_id'))
    if order.payment_status == 'paid':
        return JsonResponse({'success': False, 'error': 'This order is already paid.'}, status=400)
    method = data.get('payment_method', 'Card')
    transaction_code = data.get('transaction_code') or _fallback_code(method.upper().replace(' ', ''), order.order_number)
    _mark_order_paid(order, method, transaction_code)
    request.session['cart'] = {}
    request.session.modified = True
    return JsonResponse({
        'success': True,
        'status': 'success',
        'order_number': order.order_number,
        'receipt': transaction_code,
    })
