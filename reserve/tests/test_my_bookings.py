from datetime import date, time, timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from reserve.models import DayReservation, Reservation


class BookingListAPITests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        self.day = DayReservation.objects.create(
            date=date.today() + timedelta(days=5)
        )

        self.available_reservation = Reservation.objects.create(
            day=self.day,
            time=time(10, 30)
        )

        self.booking_url = reverse('reserve:booking')
        self.hold_url = reverse('reserve:hold')

    def test_guest_can_view_available_reservations(self):
        response = self.client.get(self.booking_url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), 1)

    def test_authenticated_user_can_view_available_reservations(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        response = self.client.get(self.booking_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_held_reservation_is_hidden_from_another_user(self):
        self.client.post(
            self.hold_url,
            {'reservation_id': self.available_reservation.id}
        )

        other_client = self.client_class()

        response = other_client.get(self.booking_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_user_can_see_own_held_reservation(self):
        self.client.post(
            self.hold_url,
            {'reservation_id': self.available_reservation.id}
        )

        response = self.client.get(self.booking_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_expired_hold_is_visible_as_available(self):
        self.client.post(
            self.hold_url,
            {'reservation_id': self.available_reservation.id}
        )

        self.available_reservation.refresh_from_db()

        self.available_reservation.hold_expires_at = (
            self.available_reservation.hold_expires_at
            - timedelta(minutes=2)
        )

        self.available_reservation.save()

        response = self.client.get(self.booking_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class MyBookingsAPITests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpassword123'
        )

        self.day = DayReservation.objects.create(
            date=date.today() + timedelta(days=5)
        )

        self.my_reservation = Reservation.objects.create(
            day=self.day,
            time=time(10, 30),
            user=self.user,
            customer_name='Test User',
            customer_email='test@example.com',
            meeting_topic='Backend consultation'
        )

        self.other_reservation = Reservation.objects.create(
            day=self.day,
            time=time(11, 30),
            user=self.other_user,
            customer_name='Other User',
            customer_email='other@example.com'
        )

        self.my_bookings_url = reverse('reserve:my-bookings')

    def test_guest_cannot_view_my_bookings(self):
        response = self.client.get(self.my_bookings_url)

        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_can_view_my_bookings(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        response = self.client.get(self.my_bookings_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_user_only_sees_own_bookings(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        response = self.client.get(self.my_bookings_url)

        reservation_ids = [
            item['id'] for item in response.data
        ]

        self.assertIn(self.my_reservation.id, reservation_ids)
        self.assertNotIn(self.other_reservation.id, reservation_ids)

    def test_my_bookings_returns_correct_customer_information(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        response = self.client.get(self.my_bookings_url)

        reservation = response.data[0]

        self.assertEqual(
            reservation['customer_name'],
            'Test User'
        )

        self.assertEqual(
            reservation['customer_email'],
            'test@example.com'
        )

        self.assertEqual(
            reservation['meeting_topic'],
            'Backend consultation'
        )