from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import admin, messages
from django.forms import modelform_factory
from django.http import JsonResponse
from django.db.models import Sum, F
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from datetime import timedelta
from functools import wraps
import json

from .models import InventoryItem, StockMovement, AuditLog, SystemLog, UserActivity
from orders.models import Order, OrderItem
from store.models import Flavor, SiteSettings
from payments.models import MpesaTransaction


def is_staff(user):
    return user.is_authenticated and user.is_staff


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/?next=' + request.path)
        if not request.user.is_staff:
            messages.error(request, 'Staff access is required for the admin panel.')
            return redirect('shop')
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_required
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


@staff_required
def inventory_list(request):
    items = InventoryItem.objects.filter(is_active=True).order_by('category', 'name')
    low_stock_items = [i for i in items if i.stock_status in ('critical', 'low')]
    return render(request, 'admin_panel/inventory.html', {
        'items': items,
        'low_stock_items': low_stock_items,
        'admin_section': 'inventory',
    })


@staff_required
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


@staff_required
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


@staff_required
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


@staff_required
def analytics_view(request):
    live_cutoff = timezone.now() - timedelta(minutes=5)
    live_sessions = UserActivity.objects.select_related('user').filter(last_seen__gte=live_cutoff)
    live_users_count = live_sessions.values('user_id').distinct().count()
    live_staff_count = live_sessions.filter(user__is_staff=True).values('user_id').distinct().count()
    live_customer_count = max(live_users_count - live_staff_count, 0)

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
        'live_users_count': live_users_count,
        'live_staff_count': live_staff_count,
        'live_customer_count': live_customer_count,
        'live_users': live_sessions.order_by('-last_seen')[:12],
        'live_window_minutes': 5,
        'admin_section': 'analytics',
    })


@staff_required
def audit_view(request):
    logs = AuditLog.objects.select_related('actor').all()[:100]
    return render(request, 'admin_panel/audit.html', {'logs': logs, 'admin_section': 'audit'})


@staff_required
def system_logs_view(request):
    level = request.GET.get('level', '')
    logger_name = request.GET.get('logger', '')
    logs = SystemLog.objects.all()
    if level:
        logs = logs.filter(level=level)
    if logger_name:
        logs = logs.filter(logger_name=logger_name)

    return render(request, 'admin_panel/system_logs.html', {
        'logs': logs[:200],
        'level': level,
        'logger_name': logger_name,
        'levels': SystemLog.LEVEL_CHOICES,
        'logger_names': SystemLog.objects.values_list('logger_name', flat=True).distinct().order_by('logger_name'),
        'admin_section': 'system_logs',
    })


@staff_required
def flavors_admin(request):
    flavors = Flavor.objects.select_related('category').all()
    return render(request, 'admin_panel/flavors.html', {'flavors': flavors, 'admin_section': 'inventory'})


@staff_required
def invoice_view(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id)
    return render(request, 'admin_panel/invoice.html', {
        'order': order,
        'issued_at': timezone.localtime(),
        'site': SiteSettings.get_settings(),
        'admin_section': 'operations',
    })


def _admin_model_registry():
    registry = []
    for model, model_admin in admin.site._registry.items():
        registry.append({
            'model': model,
            'label': model._meta.label_lower.replace('.', '/'),
            'name': model._meta.verbose_name_plural.title(),
            'app': model._meta.app_label.title(),
            'app_label': model._meta.app_label,
            'model_name': model._meta.model_name,
            'model_label': model._meta.label,
        })
    return sorted(registry, key=lambda item: (item['app'], item['name']))


def _registered_model(app_label, model_name):
    for item in _admin_model_registry():
        model = item['model']
        if model._meta.app_label == app_label and model._meta.model_name == model_name:
            return model
    return None


@staff_required
def admin_models_view(request):
    return render(request, 'admin_panel/models.html', {
        'models': _admin_model_registry(),
        'admin_section': 'system',
    })


@staff_required
def admin_model_list(request, app_label, model_name):
    model = _registered_model(app_label, model_name)
    if not model:
        messages.error(request, 'That admin model is not available.')
        return redirect('admin_models')

    objects = model.objects.all()[:200]
    fields = [field for field in model._meta.fields if field.name != 'id'][:6]
    return render(request, 'admin_panel/model_list.html', {
        'model_class': model,
        'app_label': model._meta.app_label,
        'model_name': model._meta.model_name,
        'model_label': model._meta.label,
        'verbose_name': model._meta.verbose_name.title(),
        'verbose_name_plural': model._meta.verbose_name_plural.title(),
        'objects': objects,
        'fields': fields,
        'admin_section': 'system',
    })


@staff_required
def admin_model_form(request, app_label, model_name, object_id=None):
    model = _registered_model(app_label, model_name)
    if not model:
        messages.error(request, 'That admin model is not available.')
        return redirect('admin_models')

    instance = get_object_or_404(model, pk=object_id) if object_id else None
    form_class = modelform_factory(model, fields='__all__')
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{model._meta.verbose_name.title()} saved.')
        return redirect('admin_model_list', app_label=app_label, model_name=model_name)

    return render(request, 'admin_panel/model_form.html', {
        'form': form,
        'app_label': model._meta.app_label,
        'model_name': model._meta.model_name,
        'verbose_name': model._meta.verbose_name.title(),
        'verbose_name_plural': model._meta.verbose_name_plural.title(),
        'object': instance,
        'admin_section': 'system',
    })


@staff_required
def admin_model_delete(request, app_label, model_name, object_id):
    model = _registered_model(app_label, model_name)
    if not model:
        messages.error(request, 'That admin model is not available.')
        return redirect('admin_models')
    instance = get_object_or_404(model, pk=object_id)
    if request.method == 'POST':
        try:
            instance.delete()
            messages.success(request, f'{model._meta.verbose_name.title()} deleted.')
        except ProtectedError:
            messages.error(request, 'This record is protected because other data depends on it.')
        return redirect('admin_model_list', app_label=app_label, model_name=model_name)
    return render(request, 'admin_panel/model_delete.html', {
        'app_label': model._meta.app_label,
        'model_name': model._meta.model_name,
        'verbose_name': model._meta.verbose_name.title(),
        'object': instance,
        'admin_section': 'system',
    })
