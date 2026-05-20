import time

from django.core.cache import cache
from django.http import JsonResponse


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.setdefault(
            'Content-Security-Policy',
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self'",
        )
        return response


class RateLimitMiddleware:
    RULES = [
        {'prefixes': ('/accounts/login/', '/accounts/signup/', '/profile/login/', '/profile/register/'), 'methods': ('POST',), 'limit': 8, 'window': 300, 'name': 'auth'},
        {'prefixes': ('/orders/create/',), 'methods': ('POST',), 'limit': 10, 'window': 300, 'name': 'orders'},
        {'prefixes': ('/payments/mpesa/initiate/',), 'methods': ('POST',), 'limit': 6, 'window': 300, 'name': 'mpesa-initiate'},
        {'prefixes': ('/payments/mpesa/status/',), 'methods': ('POST',), 'limit': 30, 'window': 300, 'name': 'mpesa-status'},
        {'prefixes': ('/payments/manual/complete/',), 'methods': ('POST',), 'limit': 8, 'window': 300, 'name': 'manual-payment'},
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rule = self._matching_rule(request)
        if rule:
            allowed, retry_after = self._is_allowed(request, rule)
            if not allowed:
                return JsonResponse(
                    {
                        'success': False,
                        'error': 'Too many requests. Please wait a moment and try again.',
                    },
                    status=429,
                    headers={'Retry-After': str(retry_after)},
                )
        return self.get_response(request)

    def _matching_rule(self, request):
        for rule in self.RULES:
            if request.method in rule['methods'] and any(request.path.startswith(prefix) for prefix in rule['prefixes']):
                return rule
        return None

    def _is_allowed(self, request, rule):
        key = f"rate:{rule['name']}:{self._client_key(request)}"
        now = int(time.time())
        window_start = now - rule['window']
        attempts = [stamp for stamp in cache.get(key, []) if stamp > window_start]
        if len(attempts) >= rule['limit']:
            retry_after = max(1, rule['window'] - (now - attempts[0]))
            cache.set(key, attempts, rule['window'])
            return False, retry_after
        attempts.append(now)
        cache.set(key, attempts, rule['window'])
        return True, 0

    def _client_key(self, request):
        if getattr(request, 'user', None) and request.user.is_authenticated:
            return f"user:{request.user.id}"
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip_address = forwarded_for.split(',')[0].strip() or request.META.get('REMOTE_ADDR', 'unknown')
        return f"ip:{ip_address}"
