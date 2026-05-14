import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from store.models import Flavor, SiteSettings

from .models import Order, OrderItem, OrderStatusHistory

logger = logging.getLogger(__name__)


@require_POST
def create_order(request):
    """Create order from cart data."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Please sign in or create an account before placing an order.',
            'login_url': '/accounts/login/',
        }, status=403)

    data = json.loads(request.body)

    cart = request.session.get('cart', {})
    if not cart:
        return JsonResponse({'success': False, 'error': 'Cart is empty'}, status=400)

    site = SiteSettings.get_settings()

    subtotal = sum(v['qty'] * v['price'] for v in cart.values())
    delivery_fee = float(site.delivery_fee) if subtotal > 0 else 0
    total = subtotal + delivery_fee

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        customer_name=data.get('name', ''),
        customer_email=data.get('email', ''),
        customer_phone=data.get('phone', ''),
        delivery_address=data.get('address', 'Pickup'),
        delivery_instructions=data.get('instructions', ''),
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total,
        payment_method=data.get('payment_method', 'M-Pesa'),
    )

    for item in cart.values():
        flavor = Flavor.objects.filter(id=item['id']).first()
        OrderItem.objects.create(
            order=order,
            flavor=flavor,
            flavor_name=item['name'],
            price=item['price'],
            quantity=item['qty'],
        )

    OrderStatusHistory.objects.create(
        order=order,
        status='pending',
        note='Order created, awaiting payment.',
    )
    logger.info("Order %s created by user %s for KSh %s.", order.order_number, request.user.id, order.total)

    request.session['pending_order_id'] = order.id
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'order_id': order.id,
        'order_number': order.order_number,
        'total': total,
    })


@login_required
def order_confirmation(request, order_number):
    """Order confirmation page."""
    orders = Order.objects.all() if request.user.is_staff else Order.objects.filter(user=request.user)
    order = get_object_or_404(orders, order_number=order_number)

    request.session['cart'] = {}
    request.session.modified = True

    return render(request, 'customer/order_confirmation.html', {'order': order})


@login_required
def receipt_view(request, order_number):
    """Customer receipt page."""
    orders = Order.objects.prefetch_related('items')
    if not request.user.is_staff:
        orders = orders.filter(user=request.user)
    order = get_object_or_404(orders, order_number=order_number)
    return render(request, 'customer/receipt.html', {
        'order': order,
        'issued_at': timezone.localtime(),
        'site': SiteSettings.get_settings(),
    })


@login_required
def order_status_api(request, order_number):
    """Get order status as JSON."""
    orders = Order.objects.all() if request.user.is_staff else Order.objects.filter(user=request.user)
    order = get_object_or_404(orders, order_number=order_number)
    return JsonResponse({
        'order_number': order.order_number,
        'status': order.status,
        'status_display': order.get_status_display(),
        'status_percentage': order.status_percentage,
        'payment_status': order.payment_status,
        'updated_at': order.updated_at.isoformat(),
    })


@login_required
def my_orders(request):
    """Customer orders list."""
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'customer/my_orders.html', {'orders': orders, 'active_section': 'orders'})
