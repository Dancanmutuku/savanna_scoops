from django.db import OperationalError, ProgrammingError
from django.utils import timezone


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._record_activity(request)
        return response

    def _record_activity(self, request):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return

        if not request.session.session_key:
            request.session.save()

        try:
            from .models import UserActivity

            forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
            ip_address = forwarded_for.split(',')[0].strip() or request.META.get('REMOTE_ADDR')
            UserActivity.objects.update_or_create(
                session_key=request.session.session_key,
                defaults={
                    'user': user,
                    'ip_address': ip_address or None,
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:300],
                    'path': request.path[:300],
                    'last_seen': timezone.now(),
                },
            )
        except (OperationalError, ProgrammingError):
            pass
