from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from reserve.models import DayReservation, Reservation


class BookingHoldTests(TestCase):

    def setUp(self):
        self.day = DayReservation.objects.create(
            date=date.today() + timedelta(days=5)
        )

        self.reservation = Reservation.objects.create(
            day=self.day,
            time=time(10, 30)
        )

        self.hold_url = reverse('reserve:hold')
        self.release_url = reverse('reserve:release')

    def test_user_can_hold_available_reservation(self):
        response = self.client.post(
            self.hold_url,
            {'reservation_id': self.reservation.id}
        )

        self.assertEqual(response.status_code, 200)

        self.reservation.refresh_from_db()

        self.assertIsNotNone(self.reservation.hold_token)
        self.assertIsNotNone(self.reservation.hold_expires_at)
        self.assertIsNone(self.reservation.user)

    def test_same_user_can_hold_same_reservation_again(self):
        first_response = self.client.post(
            self.hold_url,
            {'reservation_id': self.reservation.id}
        )

        self.reservation.refresh_from_db()
        first_token = self.reservation.hold_token

        second_response = self.client.post(
            self.hold_url,
            {'reservation_id': self.reservation.id}
        )

        self.reservation.refresh_from_db()

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(self.reservation.hold_token, first_token)

    def test_another_user_cannot_hold_reserved_slot(self):
        self.client.post(
            self.hold_url,
            {'reservation_id': self.reservation.id}
        )

        other_client = self.client_class()

        response = other_client.post(
            self.hold_url,
            {'reservation_id': self.reservation.id}
        )

        self.assertEqual(response.status_code, 409)

    def test_hold_nonexistent_reservation(self):
        response = self.client.post(
            self.hold_url,
            {'reservation_id': 99999}
        )

        self.assertEqual(response.status_code, 404)

    def test_hold_without_reservation_id(self):
        response = self.client.post(
            self.hold_url,
            {}
        )

        self.assertEqual(response.status_code, 400)

    def test_hold_with_invalid_reservation_id(self):
        response = self.client.post(
            self.hold_url,
            {'reservation_id': 'invalid'}
        )

        self.assertEqual(response.status_code, 400)

    def test_expired_hold_can_be_claimed_again(self):
        self.reservation.hold_token = '11111111-1111-1111-1111-111111111111'
        self.reservation.hold_expires_at = timezone.now() - timedelta(minutes=1)
        self.reservation.save()

        response = self.client.post(
            self.hold_url,
            {'reservation_id': self.reservation.id}
        )

        self.assertEqual(response.status_code, 200)

        self.reservation.refresh_from_db()

        self.assertIsNotNone(self.reservation.hold_token)
        self.assertNotEqual(
            str(self.reservation.hold_token),
            '11111111-1111-1111-1111-111111111111'
        )

    def test_user_can_release_held_reservation(self):
        hold_response = self.client.post(
            self.hold_url,
            {'reservation_id': self.reservation.id}
        )

        self.assertEqual(hold_response.status_code, 200)

        release_response = self.client.post(
            self.release_url,
            {'reservation_id': self.reservation.id}
        )

        self.assertEqual(release_response.status_code, 200)

        self.reservation.refresh_from_db()

        self.assertIsNone(self.reservation.hold_token)
        self.assertIsNone(self.reservation.hold_expires_at)
        self.assertIsNone(self.reservation.user)

    def test_user_cannot_release_another_user_hold(self):
        self.client.post(
            self.hold_url,
            {'reservation_id': self.reservation.id}
        )

        other_client = self.client_class()

        response = other_client.post(
            self.release_url,
            {'reservation_id': self.reservation.id}
        )

        self.assertEqual(response.status_code, 200)

        self.reservation.refresh_from_db()

        self.assertIsNotNone(self.reservation.hold_token)