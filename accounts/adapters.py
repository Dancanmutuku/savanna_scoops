from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if request.user.is_authenticated or sociallogin.is_existing:
            return

        email = (sociallogin.user.email or "").strip().lower()
        if not email:
            return

        user_model = sociallogin.user.__class__
        try:
            existing_user = user_model.objects.get(email__iexact=email)
        except user_model.DoesNotExist:
            return
        except user_model.MultipleObjectsReturned:
            return

        sociallogin.connect(request, existing_user)
