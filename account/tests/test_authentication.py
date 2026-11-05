from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LoginTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="StrongPass123!",
        )
        self.login_url = reverse("account:login")

    def test_login_page_returns_200(self):
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/login.html")

    def test_user_can_login_with_correct_credentials(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "testuser",
                "password": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_user_cannot_login_with_wrong_password(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "testuser",
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_user_cannot_login_with_nonexistent_username(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "unknownuser",
                "password": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_authenticated_user_is_redirected_from_login_page(self):
        self.client.force_login(self.user)

        response = self.client.get(self.login_url)

        self.assertRedirects(
            response,
            reverse("reserve:home"),
        )

    def test_login_redirects_to_next_url(self):
        response = self.client.post(
            f"{self.login_url}?next=/reserve/booking/",
            {
                "username": "testuser",
                "password": "StrongPass123!",
            },
        )

        self.assertRedirects(
            response,
            "/reserve/booking/",
            fetch_redirect_response=False,
        )


class LogoutTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="StrongPass123!",
        )
        self.logout_url = reverse("account:logout")

    def test_authenticated_user_can_logout(self):
        self.client.force_login(self.user)

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_redirects_to_home(self):
        self.client.force_login(self.user)

        response = self.client.post(self.logout_url)

        self.assertRedirects(
            response,
            reverse("reserve:home"),
        )

    def test_guest_can_access_logout_endpoint(self):
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, 302)
