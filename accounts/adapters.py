from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse


def get_sociallogin_email(sociallogin):
    """
    Return the email Google supplied for this social login.
    """

    for email_address in sociallogin.email_addresses:
        if email_address.email:
            return email_address.email.strip().lower()

    email = getattr(sociallogin.user, "email", "")

    return email.strip().lower()


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Controls how Google/social authentication interacts
    with existing and new Savanna Scoops users.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Runs after the OAuth provider has authenticated the user
        but before Allauth completes the login/signup process.

        Existing users are allowed to continue normally. New Google
        users are paused for Savanna Scoops onboarding before the local
        account and social account are saved.
        """

        if sociallogin.is_existing:
            return

        if sociallogin.account.provider != "google":
            return

        request.session["google_social_signup"] = sociallogin.serialize()
        request.session["google_social_signup_email"] = get_sociallogin_email(
            sociallogin
        )
        request.session.modified = True

        raise ImmediateHttpResponse(
            HttpResponseRedirect(reverse("google_onboarding"))
        )

    def save_user(self, request, sociallogin, form=None):
        """
        Let Allauth create and connect the social user normally, adding
        the profile fields collected during Google onboarding.
        """

        onboarding = request.session.get("google_onboarding", {})

        if onboarding:
            sociallogin.user.first_name = onboarding.get("first_name", "")
            sociallogin.user.last_name = onboarding.get("last_name", "")

        user = super().save_user(request, sociallogin, form)

        return user
