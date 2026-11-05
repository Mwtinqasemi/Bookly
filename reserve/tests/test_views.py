from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from reserve.models import DayReservation, Reservation


class HomeViewTests(TestCase):

    def test_home_page_status_code(self):
        response = self.client.get(reverse('reserve:home'))

        self.assertEqual(response.status_code, 200)

    def test_home_page_uses_correct_template(self):
        response = self.client.get(reverse('reserve:home'))

        self.assertTemplateUsed(response, 'reserve/index.html')


class BookingPageTests(TestCase):

    def test_booking_page_status_code(self):
        response = self.client.get(reverse('reserve:booking-form'))

        self.assertEqual(response.status_code, 200)

    def test_booking_page_uses_correct_template(self):
        response = self.client.get(reverse('reserve:booking-form'))

        self.assertTemplateUsed(response, 'reserve/booking.html')


class MyBookingsPageTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

    def test_guest_is_redirected_to_login(self):
        response = self.client.get(reverse('reserve:my_bookings_page'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f"{reverse('account:login')}?next={reverse('reserve:my_bookings_page')}"
        )

    def test_authenticated_user_can_access_page(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        response = self.client.get(reverse('reserve:my_bookings_page'))

        self.assertEqual(response.status_code, 200)

    def test_my_bookings_page_uses_correct_template(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        response = self.client.get(reverse('reserve:my_bookings_page'))

        self.assertTemplateUsed(response, 'reserve/my_bookings.html')