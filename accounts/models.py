from django.conf import settings
from django.db import models


class UserConsent(models.Model):
    """
    Stores the user's acceptance of the Savanna Scoops
    Terms and Conditions and Privacy Policy.
    """

    CURRENT_TERMS_VERSION = "1.0"
    CURRENT_PRIVACY_VERSION = "1.0"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consent",
    )

    terms_accepted = models.BooleanField(default=False)
    terms_version = models.CharField(
        max_length=20,
        default=CURRENT_TERMS_VERSION,
    )
    terms_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    privacy_accepted = models.BooleanField(default=False)
    privacy_version = models.CharField(
        max_length=20,
        default=CURRENT_PRIVACY_VERSION,
    )
    privacy_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Consent"
        verbose_name_plural = "User Consents"

    def __str__(self):
        return f"Consent for {self.user.email}"

    @property
    def fully_accepted(self):
        return self.terms_accepted and self.privacy_accepted


class UserProfile(models.Model):
    """
    Stores local profile details that do not belong on Django's
    built-in User model.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone_number = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile for {self.user.username}"
