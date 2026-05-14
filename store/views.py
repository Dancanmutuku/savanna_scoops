from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json

from .models import Flavor, Category, Review, SiteSettings


def shop(request):
    """Main shop / customer landing page."""
    categories = Category.objects.all()
    flavors = Flavor.objects.filter(is_active=True)
    
    # Filter by category
    category_slug = request.GET.get('category', '')
    if category_slug:
        flavors = flavors.filter(category__slug=category_slug)
    
    # Filter by search
    search = request.GET.get('q', '')
    if search:
        flavors = flavors.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    # Filter by type
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'dairy-free':
        flavors = flavors.filter(is_dairy_free=True)
    elif filter_type in ['fruity', 'creamy']:
        flavors = flavors.filter(category__slug=filter_type)

    settings_obj = SiteSettings.get_settings()
    
    context = {
        'flavors': flavors,
        'categories': categories,
        'settings': settings_obj,
        'active_section': 'shop',
        'search': search,
        'active_filter': filter_type,
        'active_category': category_slug,
    }
    return render(request, 'customer/shop.html', context)


def flavor_detail(request, slug):
    flavor = get_object_or_404(Flavor, slug=slug, is_active=True)
    reviews = flavor.reviews.select_related('user').order_by('-created_at')
    related = Flavor.objects.filter(
        category=flavor.category, is_active=True
    ).exclude(pk=flavor.pk)[:3]
    
    return render(request, 'customer/flavor_detail.html', {
        'flavor': flavor,
        'reviews': reviews,
        'related': related,
    })


@require_POST
def add_to_cart(request):
    """Add item to session cart."""
    data = json.loads(request.body)
    flavor_id = str(data.get('flavor_id'))
    
    flavor = get_object_or_404(Flavor, id=flavor_id, is_active=True)
    
    cart = request.session.get('cart', {})
    if flavor_id in cart:
        cart[flavor_id]['qty'] += 1
    else:
        cart[flavor_id] = {
            'id': flavor.id,
            'name': flavor.name,
            'price': float(flavor.price),
            'image': flavor.display_image,
            'qty': 1,
        }
    
    request.session['cart'] = cart
    request.session.modified = True
    
    total_items = sum(v['qty'] for v in cart.values())
    return JsonResponse({
        'success': True,
        'cart_count': total_items,
        'message': f'{flavor.name} added to cart!'
    })


@require_POST
def remove_from_cart(request):
    """Remove item from session cart."""
    data = json.loads(request.body)
    flavor_id = str(data.get('flavor_id'))
    
    cart = request.session.get('cart', {})
    if flavor_id in cart:
        if cart[flavor_id]['qty'] > 1:
            cart[flavor_id]['qty'] -= 1
        else:
            del cart[flavor_id]
    
    request.session['cart'] = cart
    request.session.modified = True
    
    total_items = sum(v['qty'] for v in cart.values())
    subtotal = sum(v['qty'] * v['price'] for v in cart.values())
    return JsonResponse({
        'success': True,
        'cart_count': total_items,
        'subtotal': subtotal,
    })


def cart_view(request):
    """Get cart data as JSON."""
    cart = request.session.get('cart', {})
    items = list(cart.values())
    subtotal = sum(v['qty'] * v['price'] for v in cart.values())
    settings_obj = SiteSettings.get_settings()
    delivery_fee = float(settings_obj.delivery_fee) if subtotal > 0 else 0
    return JsonResponse({
        'items': items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': subtotal + delivery_fee,
        'cart_count': sum(v['qty'] for v in cart.values()),
    })


@login_required
def checkout(request):
    """Checkout page."""
    cart = request.session.get('cart', {})
    settings_obj = SiteSettings.get_settings()
    items = list(cart.values())
    subtotal = sum(v['qty'] * v['price'] for v in cart.values())
    delivery_fee = float(settings_obj.delivery_fee) if subtotal > 0 else 0
    total = subtotal + delivery_fee
    
    context = {
        'cart_items': items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'settings': settings_obj,
        'active_section': 'checkout',
    }
    return render(request, 'customer/checkout.html', context)


def tracking(request):
    """Order tracking page."""
    order_id = request.GET.get('order_id', '')
    order = None
    
    if order_id:
        from orders.models import Order
        try:
            order = Order.objects.get(order_number=order_id)
        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')
    
    return render(request, 'customer/tracking.html', {
        'order': order,
        'order_id': order_id,
        'active_section': 'tracking',
        'stages': ['Pending', 'Confirmed', 'Preparing', 'On the Way', 'Delivered'],
    })


@login_required
@require_POST
def submit_review(request, slug):
    """Submit product review."""
    flavor = get_object_or_404(Flavor, slug=slug)
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()
    
    if not rating or not comment:
        messages.error(request, 'Please provide both rating and comment.')
        return redirect('flavor_detail', slug=slug)
    
    Review.objects.update_or_create(
        flavor=flavor, user=request.user,
        defaults={'rating': rating, 'comment': comment}
    )
    messages.success(request, 'Review submitted!')
    return redirect('flavor_detail', slug=slug)


def about(request):
    settings_obj = SiteSettings.get_settings()
    return render(request, 'customer/about.html', {'settings': settings_obj})
