from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
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


def _user_is_staff(user):
    return bool(user and user.is_authenticated and user.is_staff)


def _json_staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not _user_is_staff(getattr(request, 'user', None)):
            return JsonResponse({'success': False, 'error': 'Staff access is required.'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def _callback_token_is_valid(request):
    expected = getattr(settings, 'MPESA_CALLBACK_TOKEN', '')
    if not expected:
        return settings.DEBUG
    provided = (
        request.headers.get('X-Mpesa-Callback-Token')
        or request.GET.get('token')
        or ''
    )
    return provided == expected


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
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid request data.",
            },
            status=400,
        )

    checkout_request_id = data.get("checkout_request_id")

    if not checkout_request_id:
        return JsonResponse(
            {
                "success": False,
                "error": "No checkout ID provided.",
            },
            status=400,
        )

    # ---------------------------------------------------------
    # Find transaction
    # ---------------------------------------------------------

    try:
        txn = (
            MpesaTransaction.objects
            .select_related("order")
            .get(
                checkout_request_id=checkout_request_id
            )
        )

    except MpesaTransaction.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "error": "Transaction not found.",
            },
            status=404,
        )

    # ---------------------------------------------------------
    # Security: make sure the logged-in user owns the order
    # ---------------------------------------------------------

    if txn.order and not _user_can_access_order(
        request.user,
        txn.order,
    ):
        return JsonResponse(
            {
                "success": False,
                "error": "Transaction not found.",
            },
            status=404,
        )

    # ---------------------------------------------------------
    # If callback already confirmed payment, trust local DB
    # ---------------------------------------------------------

    if (
        txn.status == "success"
        and txn.order
        and txn.order.payment_status == "paid"
    ):
        return JsonResponse(
            {
                "success": True,
                "status": "success",
                "order_number": txn.order.order_number,
                "receipt": txn.mpesa_receipt_number or "",
                "message": "Payment confirmed.",
            }
        )

    # ---------------------------------------------------------
    # If already cancelled, don't query Safaricom again
    # ---------------------------------------------------------

    if txn.status == "cancelled":
        return JsonResponse(
            {
                "success": False,
                "status": "cancelled",
                "error": "Payment was cancelled.",
            }
        )

    # ---------------------------------------------------------
    # If already failed, return the stored failure
    # ---------------------------------------------------------

    if txn.status == "failed":
        return JsonResponse(
            {
                "success": False,
                "status": "failed",
                "error": txn.result_desc or "Payment failed.",
            }
        )

    # ---------------------------------------------------------
    # Query Safaricom
    # ---------------------------------------------------------

    try:
        result = query_stk_status(
            checkout_request_id
        )

    except Exception:
        logger.exception(
            "Unexpected M-Pesa status check failure for %s.",
            checkout_request_id,
        )

        # DO NOT mark transaction failed.
        # Safaricom may be temporarily unavailable.
        return JsonResponse(
            {
                "success": False,
                "status": "pending",
                "retry": True,
                "message": (
                    "Payment status is temporarily "
                    "unavailable. Please wait..."
                ),
            }
        )

    # ---------------------------------------------------------
    # Safaricom returned no usable response
    # ---------------------------------------------------------

    if not result:
        logger.warning(
            "Empty M-Pesa status response for %s.",
            checkout_request_id,
        )

        return JsonResponse(
            {
                "success": False,
                "status": "pending",
                "retry": True,
                "message": (
                    "Payment status is temporarily "
                    "unavailable. Please wait..."
                ),
            }
        )

    # ---------------------------------------------------------
    # Extract ResultCode
    # ---------------------------------------------------------

    result_code = _result_code_as_int(
        result.get("ResultCode")
    )

    result_desc = (
        result.get("ResultDesc")
        or result.get("error")
        or ""
    )

    # ---------------------------------------------------------
    # SUCCESS
    # ---------------------------------------------------------

    if result_code == 0:
        receipt = txn.mpesa_receipt_number

        with transaction.atomic():

            txn.status = "success"
            txn.result_code = 0

            if result_desc:
                txn.result_desc = result_desc

            txn.save(
                update_fields=[
                    "status",
                    "result_code",
                    "result_desc",
                ]
            )

            if txn.order:

                _mark_order_paid(
                    txn.order,
                    "M-Pesa",
                    receipt or _fallback_code(
                        "MPESA",
                        checkout_request_id,
                    ),
                    (
                        "Payment received via M-Pesa. "
                        f"Receipt: {receipt or 'Pending callback receipt'}"
                    ),
                )

        return JsonResponse(
            {
                "success": True,
                "status": "success",
                "order_number": (
                    txn.order.order_number
                    if txn.order
                    else ""
                ),
                "receipt": receipt or "",
                "message": "Payment confirmed.",
            }
        )
    # CUSTOMER CANCELLED STK PROMPT
    if result_code == 1032:

        with transaction.atomic():

            txn.status = "cancelled"
            txn.result_code = 1032
            txn.result_desc = (
                "User cancelled the M-Pesa payment."
            )

            txn.save(
                update_fields=[
                    "status",
                    "result_code",
                    "result_desc",
                ]
            )

            if txn.order:
                _mark_order_cancelled(
                    txn.order,
                    "M-Pesa payment was cancelled by the customer.",
                )

        return JsonResponse(
            {
                "success": False,
                "status": "cancelled",
                "error": "Payment was cancelled.",
            }
        )
    # EXPLICIT M-PESA FAILURE
    if result_code is not None:

        logger.warning(
            "M-Pesa payment failed for %s. "
            "ResultCode=%s ResultDesc=%s",
            checkout_request_id,
            result_code,
            result_desc,
        )

        with transaction.atomic():

            txn.status = "failed"
            txn.result_code = result_code
            txn.result_desc = (
                result_desc or "M-Pesa payment failed."
            )

            txn.save(
                update_fields=[
                    "status",
                    "result_code",
                    "result_desc",
                ]
            )

            if txn.order:
                _mark_order_cancelled(
                    txn.order,
                    (
                        "M-Pesa payment failed. "
                        f"{result_desc}"
                    ),
                )

        return JsonResponse(
            {
                "success": False,
                "status": "failed",
                "error": (
                    result_desc
                    or "M-Pesa payment failed."
                ),
            }
        )
    logger.warning(
        "M-Pesa status unavailable for %s. "
        "Response: %s",
        checkout_request_id,
        result,
    )

    return JsonResponse(
        {
            "success": False,
            "status": "pending",
            "retry": True,
            "message": (
                "We are still waiting for M-Pesa "
                "to confirm your payment."
            ),
        }
    )

@csrf_exempt
def mpesa_callback(request):
    """
    M-Pesa callback endpoint.

    A successful callback from Safaricom is validated using:
    - CheckoutRequestID
    - MerchantRequestID
    - M-Pesa receipt number
    - Paid amount

    We do NOT perform a second STK status query here.
    A temporary failure of the query API must not turn a
    successful payment callback into a failed payment.
    """

    if request.method != "POST":
        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "OK",
        })

    if not _callback_token_is_valid(request):
        logger.warning(
            "Rejected M-Pesa callback with invalid callback token."
        )

        return JsonResponse(
            {
                "ResultCode": 1,
                "ResultDesc": "Unauthorized",
            },
            status=403,
        )

    try:
        data = json.loads(request.body)

        callback = (
            data
            .get("Body", {})
            .get("stkCallback", {})
        )

        checkout_request_id = callback.get(
            "CheckoutRequestID"
        )

        merchant_request_id = callback.get(
            "MerchantRequestID"
        )

        result_code = callback.get(
            "ResultCode"
        )

        result_desc = callback.get(
            "ResultDesc",
            "",
        )

        if not checkout_request_id:
            logger.warning(
                "Received M-Pesa callback without CheckoutRequestID."
            )

            return JsonResponse({
                "ResultCode": 0,
                "ResultDesc": "Accepted",
            })

        try:
            txn = MpesaTransaction.objects.get(
                checkout_request_id=checkout_request_id
            )

        except MpesaTransaction.DoesNotExist:

            logger.warning(
                "M-Pesa callback for unknown transaction: %s",
                checkout_request_id,
            )

            return JsonResponse({
                "ResultCode": 0,
                "ResultDesc": "Accepted",
            })

        # ---------------------------------------------------------
        # Validate MerchantRequestID
        # ---------------------------------------------------------

        if (
            merchant_request_id
            and txn.merchant_request_id
            and merchant_request_id != txn.merchant_request_id
        ):
            logger.warning(
                "Rejected M-Pesa callback for %s due to "
                "merchant request mismatch.",
                checkout_request_id,
            )

            return JsonResponse({
                "ResultCode": 0,
                "ResultDesc": "Accepted",
            })

        result_code_int = _result_code_as_int(
            result_code
        )

        txn.result_code = result_code_int
        txn.result_desc = result_desc

        # =========================================================
        # SUCCESSFUL PAYMENT
        # =========================================================

        if result_code_int == 0:

            # Prevent duplicate processing
            if (
                txn.status == "success"
                and txn.order
                and txn.order.payment_status == "paid"
            ):
                logger.info(
                    "Ignoring duplicate M-Pesa success callback "
                    "for %s.",
                    checkout_request_id,
                )

                return JsonResponse({
                    "ResultCode": 0,
                    "ResultDesc": "Accepted",
                })

            # -----------------------------------------------------
            # Get actual M-Pesa receipt
            # -----------------------------------------------------

            receipt = _callback_metadata_value(
                callback,
                "MpesaReceiptNumber",
            )

            if not receipt:
                txn.status = "failed"
                txn.result_desc = (
                    "Missing M-Pesa receipt number."
                )
                txn.save()

                logger.warning(
                    "Rejected M-Pesa callback for %s because "
                    "receipt number was missing.",
                    checkout_request_id,
                )

                return JsonResponse({
                    "ResultCode": 0,
                    "ResultDesc": "Accepted",
                })

            # -----------------------------------------------------
            # Get actual amount paid
            # -----------------------------------------------------

            paid_amount = _decimal_or_none(
                _callback_metadata_value(
                    callback,
                    "Amount",
                )
            )

            if paid_amount is None:
                txn.status = "failed"
                txn.result_desc = (
                    "Missing or invalid paid amount."
                )
                txn.save()

                logger.warning(
                    "Rejected M-Pesa callback for %s because "
                    "amount was missing or invalid.",
                    checkout_request_id,
                )

                return JsonResponse({
                    "ResultCode": 0,
                    "ResultDesc": "Accepted",
                })

            # -----------------------------------------------------
            # Verify amount
            # -----------------------------------------------------

            if (
                txn.order
                and paid_amount != txn.order.total
            ):
                txn.status = "failed"
                txn.result_code = result_code_int
                txn.result_desc = (
                    f"Amount mismatch. "
                    f"Paid {paid_amount}, "
                    f"expected {txn.order.total}."
                )

                txn.save()

                logger.warning(
                    "Rejected M-Pesa callback for %s due to "
                    "amount mismatch. Paid: %s Expected: %s",
                    checkout_request_id,
                    paid_amount,
                    txn.order.total,
                )

                return JsonResponse({
                    "ResultCode": 0,
                    "ResultDesc": "Accepted",
                })

            # =====================================================
            # PAYMENT IS VALID
            # =====================================================

            with transaction.atomic():

                txn.status = "success"
                txn.result_code = result_code_int
                txn.result_desc = result_desc
                txn.mpesa_receipt_number = receipt

                txn.save()

                if txn.order:

                    _mark_order_paid(
                        txn.order,
                        "M-Pesa",
                        receipt,
                        (
                            "M-Pesa payment confirmed. "
                            f"Receipt: {receipt}"
                        ),
                    )

            logger.info(
                "M-Pesa payment successfully confirmed. "
                "Checkout: %s | Receipt: %s | Amount: %s",
                checkout_request_id,
                receipt,
                paid_amount,
            )

        # =========================================================
        # CUSTOMER CANCELLED PAYMENT
        # =========================================================

        elif result_code_int == 1032:

            with transaction.atomic():

                txn.status = "cancelled"
                txn.result_code = result_code_int
                txn.result_desc = result_desc
                txn.save()

                if txn.order:

                    _mark_order_cancelled(
                        txn.order,
                        "M-Pesa prompt was cancelled by the customer.",
                    )

            logger.info(
                "M-Pesa payment cancelled by customer: %s",
                checkout_request_id,
            )

        # =========================================================
        # OTHER M-PESA FAILURE
        # =========================================================

        else:

            txn.status = "failed"
            txn.result_code = result_code_int
            txn.result_desc = result_desc
            txn.save()

            logger.warning(
                "M-Pesa payment failed. "
                "Checkout: %s | Code: %s | Description: %s",
                checkout_request_id,
                result_code_int,
                result_desc,
            )

        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Accepted",
        })

    except json.JSONDecodeError:
        logger.exception(
            "Invalid JSON received from M-Pesa callback."
        )

        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Accepted",
        })

    except Exception:
        logger.exception(
            "Unexpected error while processing M-Pesa callback."
        )

        # Always acknowledge the callback so Safaricom does not
        # repeatedly resend it because of an application error.
        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Accepted",
        })

@require_POST
@login_required
@_json_staff_required
def complete_manual_payment(request):
    """Mark an order paid for non-M-Pesa checkout methods."""
    data = json.loads(request.body)
    order = get_object_or_404(Order, id=data.get('order_id'))
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
