from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class UsernameOrEmailBackend(ModelBackend):
    """Authenticate a user with username, email address, or phone number."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (username or kwargs.get('email') or '').strip()
        if not identifier or not password:
            return None

        phone_identifier = (
            identifier
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        user = User.objects.filter(
            Q(username__iexact=identifier)
            | Q(email__iexact=identifier)
            | Q(profile__phone_number__iexact=phone_identifier)
        ).first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
