from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import json

from .models import Order, OrderItem, OrderStatusHistory
from store.models import Flavor, SiteSettings


@require_POST
def create_order(request):
    """Create order from cart data."""
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
    
    for flavor_id, item in cart.items():
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
    
    # Store order_id in session for payment reference
    request.session['pending_order_id'] = order.id
    request.session.modified = True
    
    return JsonResponse({
        'success': True,
        'order_id': order.id,
        'order_number': order.order_number,
        'total': total,
    })


def order_confirmation(request, order_number):
    """Order confirmation page."""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Clear cart
    request.session['cart'] = {}
    request.session.modified = True
    
    # Send email
    try:
        _send_confirmation_email(order)
    except Exception:
        pass  # Email is best-effort
    
    return render(request, 'customer/order_confirmation.html', {'order': order})


def receipt_view(request, order_number):
    """Customer receipt page."""
    order = get_object_or_404(Order.objects.prefetch_related('items'), order_number=order_number)
    return render(request, 'customer/receipt.html', {
        'order': order,
        'issued_at': timezone.localtime(),
        'site': SiteSettings.get_settings(),
    })


def order_status_api(request, order_number):
    """Get order status as JSON."""
    order = get_object_or_404(Order, order_number=order_number)
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
    return render(request, 'customer/my_orders.html', {'orders': orders})


def _send_confirmation_email(order):
    subject = f'Order Confirmed – {order.order_number} | Savanna Scoops'
    body = render_to_string('emails/order_confirmation.html', {'order': order})
    send_mail(
        subject, '', settings.DEFAULT_FROM_EMAIL,
        [order.customer_email],
        html_message=body, fail_silently=True
    )
