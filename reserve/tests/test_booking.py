from datetime import date, time, timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from reserve.models import DayReservation, Reservation


class BookingTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        self.day = DayReservation.objects.create(
            date=date.today() + timedelta(days=5)
        )

        self.reservation = Reservation.objects.create(
            day=self.day,
            time=time(10, 30)
        )

        self.booking_url = reverse('reserve:booking')

        self.hold_url = reverse('reserve:hold')

    def hold_reservation(self):
        return self.client.post(
            self.hold_url,
            {'reservation_id': self.reservation.id}
        )

    def test_authenticated_user_can_book_reservation(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        self.hold_reservation()

        response = self.client.post(
            self.booking_url,
            {
                'reservation_id': self.reservation.id,
                'customer_name': 'Test User',
                'customer_email': 'test@example.com',
                'meeting_topic': 'Backend consultation'
            }
        )

        self.assertEqual(response.status_code, 200)

        self.reservation.refresh_from_db()

        self.assertEqual(self.reservation.user, self.user)
        self.assertEqual(self.reservation.customer_name, 'Test User')
        self.assertEqual(
            self.reservation.customer_email,
            'test@example.com'
        )
        self.assertEqual(
            self.reservation.meeting_topic,
            'Backend consultation'
        )

    def test_guest_cannot_book_reservation(self):
        response = self.client.post(
            self.booking_url,
            {
                'reservation_id': self.reservation.id,
                'customer_name': 'Test User',
                'customer_email': 'test@example.com'
            }
        )

        self.assertEqual(response.status_code, 403)

    def test_user_cannot_book_without_hold(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        response = self.client.post(
            self.booking_url,
            {
                'reservation_id': self.reservation.id,
                'customer_name': 'Test User',
                'customer_email': 'test@example.com'
            }
        )

        self.assertEqual(response.status_code, 409)

    def test_user_cannot_book_with_invalid_hold_token(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        other_client = self.client_class()
        other_client.post(
            self.hold_url,
            {'reservation_id': self.reservation.id}
        )

        response = self.client.post(
            self.booking_url,
            {
                'reservation_id': self.reservation.id,
                'customer_name': 'Test User',
                'customer_email': 'test@example.com'
            }
        )

        self.assertEqual(response.status_code, 409)

    def test_booking_requires_customer_name(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        self.hold_reservation()

        response = self.client.post(
            self.booking_url,
            {
                'reservation_id': self.reservation.id,
                'customer_name': '',
                'customer_email': 'test@example.com'
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_booking_requires_customer_email(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        self.hold_reservation()

        response = self.client.post(
            self.booking_url,
            {
                'reservation_id': self.reservation.id,
                'customer_name': 'Test User',
                'customer_email': ''
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_expired_hold_cannot_be_booked(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        self.hold_reservation()

        self.reservation.refresh_from_db()

        self.reservation.hold_expires_at = (
            timezone.now() - timedelta(minutes=1)
        )

        self.reservation.save()

        response = self.client.post(
            self.booking_url,
            {
                'reservation_id': self.reservation.id,
                'customer_name': 'Test User',
                'customer_email': 'test@example.com'
            }
        )

        self.assertEqual(response.status_code, 409)

    def test_successful_booking_clears_hold_information(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        self.hold_reservation()

        response = self.client.post(
            self.booking_url,
            {
                'reservation_id': self.reservation.id,
                'customer_name': 'Test User',
                'customer_email': 'test@example.com'
            }
        )

        self.assertEqual(response.status_code, 200)

        self.reservation.refresh_from_db()

        self.assertIsNone(self.reservation.hold_token)
        self.assertIsNone(self.reservation.hold_expires_at)

    def test_booked_reservation_cannot_be_booked_again(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        self.hold_reservation()

        first_response = self.client.post(
            self.booking_url,
            {
                'reservation_id': self.reservation.id,
                'customer_name': 'Test User',
                'customer_email': 'test@example.com'
            }
        )

        self.assertEqual(first_response.status_code, 200)

        second_response = self.client.post(
            self.booking_url,
            {
                'reservation_id': self.reservation.id,
                'customer_name': 'Another User',
                'customer_email': 'another@example.com'
            }
        )

        self.assertEqual(second_response.status_code, 409)