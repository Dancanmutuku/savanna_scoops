from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.urls import get_resolver
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from allauth.account.utils import complete_signup
from allauth.socialaccount import app_settings as socialaccount_settings
from allauth.socialaccount.adapter import get_adapter as get_socialaccount_adapter
from allauth.socialaccount.models import SocialLogin

from .models import UserConsent


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        label="Password",
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password",
    )

    first_name = forms.CharField(
        max_length=100,
        required=True,
    )

    last_name = forms.CharField(
        max_length=100,
        required=True,
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean(self):
        data = super().clean()

        p1 = data.get("password1")
        p2 = data.get("password2")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(
                "Passwords do not match."
            )

        return data

    def save(self, commit=True):
        user = super().save(commit=False)

        email = self.cleaned_data["email"].strip().lower()

        user.username = email
        user.email = email

        user.set_password(
            self.cleaned_data["password1"]
        )

        if commit:
            user.save()

        return user


class GoogleOnboardingForm(forms.Form):
    """
    Information collected from a new Google user
    before completing account creation.
    """

    first_name = forms.CharField(
        max_length=100,
        required=True,
        label="First name",
    )

    last_name = forms.CharField(
        max_length=100,
        required=True,
        label="Last name",
    )

    phone_number = forms.CharField(
        max_length=30,
        required=False,
        label="Phone number",
    )

    accept_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms and Conditions.",
        error_messages={
            "required": "You must accept the Terms and Conditions."
        },
    )

    accept_privacy = forms.BooleanField(
        required=True,
        label="I acknowledge the Privacy Policy.",
        error_messages={
            "required": "You must acknowledge the Privacy Policy."
        },
    )


def login_view(request):
    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or "/"
    )

    if request.user.is_authenticated:

        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
        ):

            if (
                not next_url.startswith("/admin-panel/")
                or request.user.is_staff
            ):
                return redirect(next_url)

            messages.error(
                request,
                "Staff access is required for the admin panel.",
            )

        return redirect("shop")

    if request.method == "POST":

        identifier = request.POST.get(
            "email",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

        user = authenticate(
            request,
            username=identifier,
            password=password,
        )

        if user:

            login(request, user)

            if url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
            ):
                return redirect(next_url)

            return redirect("shop")

        messages.error(
            request,
            "Invalid username/email or password.",
        )

    google_app = (
        settings.SOCIALACCOUNT_PROVIDERS
        .get("google", {})
        .get("APP", {})
    )

    google_enabled = bool(
        google_app.get("client_id")
        and google_app.get("secret")
    )

    if google_enabled:

        try:
            from allauth.socialaccount.providers.google import urls as google_urls  # noqa: F401

            reverse_dict = (
                get_resolver().reverse_dict
            )

            google_enabled = any(
                isinstance(name, str)
                and name.startswith("google_")
                for name in reverse_dict.keys()
            )

        except Exception:
            google_enabled = False

    return render(
        request,
        "accounts/login.html",
        {
            "next": next_url,
            "google_enabled": google_enabled,
        },
    )


def register_view(request):

    if request.user.is_authenticated:
        return redirect("shop")

    form = RegisterForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        user = form.save()

        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )

        messages.success(
            request,
            f"Welcome to Savanna Scoops, {user.first_name}!",
        )

        return redirect("shop")

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


def google_onboarding_view(request):
    """
    Onboarding page for a new Google user.

    IMPORTANT:
    This view should only be reachable as part of the
    Google social signup flow.
    """

    if request.user.is_authenticated:
        return redirect("shop")

    pending_social_signup = request.session.get(
        "google_social_signup"
    )

    if not pending_social_signup:
        messages.error(
            request,
            "Your Google signup session has expired. Please try again.",
        )

        return redirect("account_login")

    pending_sociallogin = SocialLogin.deserialize(
        pending_social_signup
    )

    initial = {
        "first_name": pending_sociallogin.user.first_name,
        "last_name": pending_sociallogin.user.last_name,
    }

    form = GoogleOnboardingForm(
        request.POST or None,
        initial=initial,
    )

    if request.method == "POST":

        if form.is_valid():

            request.session["google_onboarding"] = {
                "first_name": form.cleaned_data[
                    "first_name"
                ].strip(),

                "last_name": form.cleaned_data[
                    "last_name"
                ].strip(),

                "phone_number": form.cleaned_data[
                    "phone_number"
                ].strip(),

                "terms_accepted": True,

                "terms_version": (
                    UserConsent.CURRENT_TERMS_VERSION
                ),

                "privacy_accepted": True,

                "privacy_version": (
                    UserConsent.CURRENT_PRIVACY_VERSION
                ),
            }

            request.session.modified = True

            return redirect(
                "google_onboarding_complete"
            )

    return render(
        request,
        "accounts/google_onboarding.html",
        {
            "form": form,
            "email": request.session.get(
                "google_social_signup_email",
                pending_sociallogin.user.email,
            ),
        },
    )


def google_onboarding_complete(request):
    """
    Completes the onboarding process after the user
    has accepted the Terms and Privacy Policy.

    This endpoint validates the temporary onboarding
    information before creating the local Django user.
    """

    if request.user.is_authenticated:
        return redirect("shop")

    pending_social_signup = request.session.get(
        "google_social_signup"
    )

    onboarding = request.session.get(
        "google_onboarding"
    )

    if not pending_social_signup or not onboarding:
        messages.error(
            request,
            "Your Google signup session has expired. Please try again.",
        )

        return redirect("account_login")

    sociallogin = SocialLogin.deserialize(
        pending_social_signup
    )

    email = sociallogin.user.email.strip().lower()

    if not email and sociallogin.email_addresses:
        email = sociallogin.email_addresses[0].email.strip().lower()

    if not email:
        messages.error(
            request,
            "Google did not provide an email address.",
        )

        return redirect("account_login")

    if User.objects.filter(
        email__iexact=email
    ).exists():

        messages.info(
            request,
            "An account with this email already exists. Please sign in.",
        )

        request.session.pop(
            "google_social_signup",
            None,
        )

        request.session.pop(
            "google_social_signup_email",
            None,
        )

        request.session.pop(
            "google_onboarding",
            None,
        )

        request.session.modified = True

        return redirect("account_login")

    user = get_socialaccount_adapter(request).save_user(
        request,
        sociallogin,
        form=None,
    )

    UserConsent.objects.create(
        user=user,

        terms_accepted=True,
        terms_version=onboarding.get(
            "terms_version",
            UserConsent.CURRENT_TERMS_VERSION,
        ),
        terms_accepted_at=timezone.now(),

        privacy_accepted=True,
        privacy_version=onboarding.get(
            "privacy_version",
            UserConsent.CURRENT_PRIVACY_VERSION,
        ),
        privacy_accepted_at=timezone.now(),
    )

    request.session.pop(
        "google_social_signup",
        None,
    )

    request.session.pop(
        "google_social_signup_email",
        None,
    )

    request.session.pop(
        "google_onboarding",
        None,
    )

    request.session.modified = True

    messages.success(
        request,
        f"Welcome to Savanna Scoops, {user.first_name}!",
    )

    return complete_signup(
        request,
        user,
        socialaccount_settings.EMAIL_VERIFICATION,
        sociallogin.get_redirect_url(request),
        signal_kwargs={"sociallogin": sociallogin},
    )


def logout_view(request):
    logout(request)
    return redirect("shop")


@login_required
def profile_view(request, username=None):

    from orders.models import Order

    if username and username not in {
        request.user.username,
        request.user.email,
    }:

        messages.error(
            request,
            "You can only view your own profile.",
        )

        return redirect("profile")

    if request.method == "POST":

        request.user.first_name = (
            request.POST.get(
                "first_name",
                "",
            ).strip()
        )

        request.user.last_name = (
            request.POST.get(
                "last_name",
                "",
            ).strip()
        )

        request.user.save()

        messages.success(
            request,
            "Profile updated!",
        )

    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items")[:10]
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "orders": orders,
        },
    )
