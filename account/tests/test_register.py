from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from account.models import Profile


class RegisterTests(TestCase):

    def setUp(self):
        self.register_url = reverse("account:register")

        self.valid_data = {
            "username": "testuser",
            "full_name": "Test User",
            "phone": "09123456789",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }

    def test_register_page_returns_200(self):
        response = self.client.get(self.register_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/register.html")

    def test_user_can_register_successfully(self):
        response = self.client.post(
            self.register_url,
            self.valid_data,
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            User.objects.filter(username="testuser").exists()
        )

        self.assertTrue(
            Profile.objects.filter(
                user__username="testuser",
                phone="09123456789",
            ).exists()
        )

    def test_user_is_logged_in_after_registration(self):
        self.client.post(
            self.register_url,
            self.valid_data,
        )

        user = User.objects.get(username="testuser")

        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            user.id,
        )

    def test_registration_with_existing_username_fails(self):
        User.objects.create_user(
            username="testuser",
            password="ExistingPass123!",
        )

        response = self.client.post(
            self.register_url,
            self.valid_data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Profile.objects.filter(phone="09123456789").exists()
        )

    def test_registration_with_existing_phone_fails(self):
        existing_user = User.objects.create_user(
            username="existinguser",
            password="ExistingPass123!",
        )

        Profile.objects.create(
            user=existing_user,
            phone="09123456789",
        )

        response = self.client.post(
            self.register_url,
            self.valid_data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(username="testuser").exists()
        )

    def test_registration_with_different_passwords_fails(self):
        data = self.valid_data.copy()
        data["password2"] = "DifferentPass123!"

        response = self.client.post(
            self.register_url,
            data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(username="testuser").exists()
        )

    def test_authenticated_user_cannot_access_register_page(self):
        user = User.objects.create_user(
            username="loggeduser",
            password="StrongPass123!",
        )

        self.client.force_login(user)

        response = self.client.get(self.register_url)

        self.assertRedirects(
            response,
            reverse("reserve:home"),
        )

    def test_register_redirects_to_next_url(self):
        data = self.valid_data.copy()
        data["username"] = "nextuser"

        response = self.client.post(
            f"{self.register_url}?next=/reserve/booking/",
            data,
        )

        self.assertRedirects(
            response,
            "/reserve/booking/",
            fetch_redirect_response=False,
        )

    def test_register_rejects_external_next_url(self):
        data = self.valid_data.copy()
        data["username"] = "externaluser"

        response = self.client.post(
            f"{self.register_url}?next=https://example.com",
            data,
        )

        self.assertRedirects(
            response,
            reverse("reserve:home"),
        )
