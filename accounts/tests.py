from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from .models import UserProfile


@override_settings(DEBUG=False)
class AccountIdentifierTests(TestCase):
    def test_user_can_register_with_username_password_and_phone_only(self):
        response = self.client.post(
            "/accounts/signup/",
            {
                "first_name": "Jane",
                "last_name": "Mwangi",
                "username": "janemwangi",
                "email": "",
                "phone_number": "+254 712 345 678",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)

        user = User.objects.get(username="janemwangi")

        self.assertEqual(user.email, "")
        self.assertEqual(user.profile.phone_number, "+254712345678")

    def test_password_login_accepts_username_email_or_phone(self):
        user = User.objects.create_user(
            username="janemwangi",
            email="jane@example.com",
            password="StrongPass123!",
        )
        UserProfile.objects.create(
            user=user,
            phone_number="+254712345678",
        )

        identifiers = [
            "janemwangi",
            "jane@example.com",
            "+254 712 345 678",
        ]

        for identifier in identifiers:
            with self.subTest(identifier=identifier):
                authenticated_user = authenticate(
                    username=identifier,
                    password="StrongPass123!",
                )

                self.assertEqual(authenticated_user, user)
