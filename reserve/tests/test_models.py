from datetime import date, time

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from reserve.models import DayReservation, Reservation


class DayReservationModelTests(TestCase):

    def test_create_day_reservation(self):
        day = DayReservation.objects.create(
            date=date(2026, 11, 10)
        )

        self.assertEqual(day.date, date(2026, 11, 10))
        self.assertEqual(DayReservation.objects.count(), 1)

    def test_string_representation(self):
        day = DayReservation.objects.create(
            date=date(2026, 11, 10)
        )

        self.assertEqual(str(day), '2026-11-10')

    def test_ordering_by_date_descending(self):
        day1 = DayReservation.objects.create(
            date=date(2026, 11, 10)
        )
        day2 = DayReservation.objects.create(
            date=date(2026, 11, 12)
        )
        day3 = DayReservation.objects.create(
            date=date(2026, 11, 11)
        )

        days = list(DayReservation.objects.all())

        self.assertEqual(days, [day2, day3, day1])


class ReservationModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123'
        )

        self.day = DayReservation.objects.create(
            date=date(2026, 11, 10)
        )

    def test_create_reservation(self):
        reservation = Reservation.objects.create(
            day=self.day,
            time=time(10, 30),
            user=self.user,
            customer_name='Test User',
            customer_email='test@example.com',
            meeting_topic='Backend Development'
        )

        self.assertEqual(reservation.day, self.day)
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.time, time(10, 30))
        self.assertEqual(reservation.customer_name, 'Test User')
        self.assertEqual(reservation.customer_email, 'test@example.com')
        self.assertEqual(
            reservation.meeting_topic,
            'Backend Development'
        )

    def test_reservation_can_be_created_without_user(self):
        reservation = Reservation.objects.create(
            day=self.day,
            time=time(11, 30)
        )

        self.assertIsNone(reservation.user)
        self.assertEqual(reservation.customer_name, '')
        self.assertEqual(reservation.customer_email, '')

    def test_hold_fields_are_empty_by_default(self):
        reservation = Reservation.objects.create(
            day=self.day,
            time=time(12, 30)
        )

        self.assertIsNone(reservation.hold_token)
        self.assertIsNone(reservation.hold_expires_at)

    def test_string_representation(self):
        reservation = Reservation.objects.create(
            day=self.day,
            time=time(10, 30)
        )

        self.assertEqual(
            str(reservation),
            '2026-11-10 - 10:30:00'
        )

    def test_ordering_by_time_ascending(self):
        reservation1 = Reservation.objects.create(
            day=self.day,
            time=time(14, 30)
        )

        reservation2 = Reservation.objects.create(
            day=self.day,
            time=time(9, 30)
        )

        reservation3 = Reservation.objects.create(
            day=self.day,
            time=time(12, 30)
        )

        reservations = list(Reservation.objects.all())

        self.assertEqual(
            reservations,
            [reservation2, reservation3, reservation1]
        )

    def test_duplicate_day_and_time_is_not_allowed(self):
        Reservation.objects.create(
            day=self.day,
            time=time(10, 30)
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Reservation.objects.create(
                    day=self.day,
                    time=time(10, 30)
                )

    def test_same_time_on_different_days_is_allowed(self):
        another_day = DayReservation.objects.create(
            date=date(2026, 11, 11)
        )

        Reservation.objects.create(
            day=self.day,
            time=time(10, 30)
        )

        reservation = Reservation.objects.create(
            day=another_day,
            time=time(10, 30)
        )

        self.assertEqual(Reservation.objects.count(), 2)
        self.assertEqual(reservation.day, another_day)

    def test_deleting_day_deletes_its_reservations(self):
        Reservation.objects.create(
            day=self.day,
            time=time(10, 30)
        )

        self.day.delete()

        self.assertEqual(Reservation.objects.count(), 0)
