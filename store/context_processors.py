from .models import SiteSettings


def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(v['qty'] for v in cart.values())
    return {'cart_count': count}


def site_settings(request):
    settings = SiteSettings.get_settings()
    return {'site_settings': settings}
