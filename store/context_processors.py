from .models import SiteSettings
from django.core.cache import cache


def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(v['qty'] for v in cart.values())
    return {'cart_count': count}


def site_settings(request):
    settings = cache.get('store:site-settings')
    if settings is None:
        settings = SiteSettings.get_settings()
        cache.set('store:site-settings', settings, 300)
    return {'site_settings': settings}
