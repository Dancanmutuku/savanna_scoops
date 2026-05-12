from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
import json

from .models import InventoryItem, StockMovement, AuditLog
from orders.models import Order, OrderItem
from store.models import Flavor, SiteSettings
from payments.models import MpesaTransaction


def is_staff(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_staff, login_url='/accounts/login/')
def admin_dashboard(request):
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    orders_today = Order.objects.filter(created_at__date=today, payment_status='paid')
    daily_revenue = orders_today.aggregate(total=Sum('total'))['total'] or 0

    orders_yesterday = Order.objects.filter(created_at__date=yesterday, payment_status='paid')
    yesterday_revenue = orders_yesterday.aggregate(total=Sum('total'))['total'] or 0

    revenue_trend = 0
    if yesterday_revenue:
        revenue_trend = round(
            ((float(daily_revenue) - float(yesterday_revenue)) / float(yesterday_revenue)) * 100, 1
        )

    active_orders = Order.objects.filter(
        status__in=['confirmed', 'preparing', 'out_for_delivery']
    ).count()

    low_stock = InventoryItem.objects.filter(is_active=True).filter(current_stock__lte=F('min_stock'))
    recent_transactions = Order.objects.prefetch_related('items').order_by('-created_at')[:10]
    audit_logs = AuditLog.objects.select_related('actor').order_by('-created_at')[:8]
    top_flavors = Flavor.objects.filter(is_active=True).order_by('-total_sales')[:5]

    monthly_data = []
    for i in range(7, -1, -1):
        day = today - timedelta(days=i)
        rev = Order.objects.filter(
            created_at__date=day, payment_status='paid'
        ).aggregate(total=Sum('total'))['total'] or 0
        monthly_data.append({'date': day.strftime('%d/%m'), 'revenue': float(rev)})

    total_customers = Order.objects.values('customer_email').distinct().count()
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(total=Sum('total'))['total'] or 0

    context = {
        'daily_revenue': daily_revenue,
        'revenue_trend': revenue_trend,
        'active_orders': active_orders,
        'low_stock_count': low_stock.count(),
        'recent_transactions': recent_transactions,
        'audit_logs': audit_logs,
        'top_flavors': top_flavors,
        'monthly_data': json.dumps(monthly_data),
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'admin_section': 'dashboard',
    }
    return render(request, 'admin_panel/dashboard.html', context)


@user_passes_test(is_staff, login_url='/accounts/login/')
def inventory_list(request):
    items = InventoryItem.objects.filter(is_active=True).order_by('category', 'name')
    low_stock_items = [i for i in items if i.stock_status in ('critical', 'low')]
    return render(request, 'admin_panel/inventory.html', {
        'items': items,
        'low_stock_items': low_stock_items,
        'admin_section': 'inventory',
    })


@user_passes_test(is_staff, login_url='/accounts/login/')
def inventory_update(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    data = json.loads(request.body)
    new_stock = data.get('stock')
    movement_type = data.get('type', 'adjustment')
    notes = data.get('notes', '')
    old_stock = item.current_stock
    item.current_stock = new_stock
    item.save()
    StockMovement.objects.create(
        item=item, movement_type=movement_type,
        quantity=abs(float(new_stock) - float(old_stock)),
        previous_stock=old_stock, new_stock=new_stock,
        notes=notes, created_by=request.user,
    )
    AuditLog.objects.create(
        actor=request.user,
        actor_name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
        actor_role='Staff', action=f'Updated stock for {item.name}',
        module='Inventory', severity='info',
        impact=f'Stock: {old_stock} → {new_stock} {item.unit}',
        ip_address=request.META.get('REMOTE_ADDR'),
    )
    return JsonResponse({'success': True, 'new_stock': float(new_stock), 'status': item.stock_status})


@user_passes_test(is_staff, login_url='/accounts/login/')
def orders_admin(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.prefetch_related('items').all()
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'admin_panel/orders.html', {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
        'admin_section': 'operations',
    })


@user_passes_test(is_staff, login_url='/accounts/login/')
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    data = json.loads(request.body)
    new_status = data.get('status')
    order.status = new_status
    order.save()
    from orders.models import OrderStatusHistory
    OrderStatusHistory.objects.create(
        order=order, status=new_status,
        updated_by=request.user, note=data.get('note', ''),
    )
    return JsonResponse({'success': True, 'status': new_status, 'display': order.get_status_display()})


@user_passes_test(is_staff, login_url='/accounts/login/')
def analytics_view(request):
    flavor_sales = OrderItem.objects.values('flavor_name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('subtotal'),
    ).order_by('-total_revenue')[:10]

    today = timezone.now().date()
    daily_revenue = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        rev = Order.objects.filter(
            created_at__date=day, payment_status='paid'
        ).aggregate(total=Sum('total'))['total'] or 0
        daily_revenue.append({'date': day.strftime('%b %d'), 'revenue': float(rev)})

    total_revenue = Order.objects.filter(payment_status='paid').aggregate(total=Sum('total'))['total'] or 0
    total_orders = Order.objects.count()
    paid_orders = Order.objects.filter(payment_status='paid').count()

    return render(request, 'admin_panel/analytics.html', {
        'flavor_sales': list(flavor_sales),
        'daily_revenue': json.dumps(daily_revenue),
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'paid_orders': paid_orders,
        'admin_section': 'analytics',
    })


@user_passes_test(is_staff, login_url='/accounts/login/')
def audit_view(request):
    logs = AuditLog.objects.select_related('actor').all()[:100]
    return render(request, 'admin_panel/audit.html', {'logs': logs, 'admin_section': 'audit'})


@user_passes_test(is_staff, login_url='/accounts/login/')
def flavors_admin(request):
    flavors = Flavor.objects.select_related('category').all()
    return render(request, 'admin_panel/flavors.html', {'flavors': flavors, 'admin_section': 'inventory'})
