from datetime import date, time, timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from reserve.models import DayReservation, Reservation


class CancelBookingTests(TestCase):

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

        self.reservation = Reservation.objects.create(
            day=self.day,
            time=time(10, 30),
            user=self.user,
            customer_name='Test User',
            customer_email='test@example.com',
            meeting_topic='Backend consultation'
        )

        self.cancel_url = reverse(
            'reserve:delete-booking',
            kwargs={'reservation_id': self.reservation.id}
        )

    def test_authenticated_user_can_cancel_own_booking(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        response = self.client.delete(self.cancel_url)

        self.assertEqual(response.status_code, 200)

        self.reservation.refresh_from_db()

        self.assertIsNone(self.reservation.user)

    def test_guest_cannot_cancel_booking(self):
        response = self.client.delete(self.cancel_url)

        self.assertEqual(response.status_code, 403)

    def test_user_cannot_cancel_another_users_booking(self):
        self.client.login(
            username='otheruser',
            password='testpassword123'
        )

        response = self.client.delete(self.cancel_url)

        self.assertEqual(response.status_code, 404)

        self.reservation.refresh_from_db()

        self.assertEqual(self.reservation.user, self.user)

    def test_cancel_clears_customer_information(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        response = self.client.delete(self.cancel_url)

        self.assertEqual(response.status_code, 200)

        self.reservation.refresh_from_db()

        self.assertEqual(self.reservation.customer_name, '')
        self.assertEqual(self.reservation.customer_email, '')
        self.assertEqual(self.reservation.meeting_topic, '')

    def test_cancel_clears_hold_information(self):
        self.reservation.hold_token = '11111111-1111-1111-1111-111111111111'
        self.reservation.hold_expires_at = (
            self.reservation.day.date
        )

        # برای این تست فقط بررسی پاک شدن اطلاعات Hold اهمیت دارد.
        # مقدار تاریخ را به یک datetime معتبر تبدیل می‌کنیم.
        from django.utils import timezone
        from datetime import datetime, time as datetime_time

        self.reservation.hold_expires_at = timezone.make_aware(
            datetime.combine(
                date.today(),
                datetime_time(12, 0)
            )
        )

        self.reservation.save()

        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        response = self.client.delete(self.cancel_url)

        self.assertEqual(response.status_code, 200)

        self.reservation.refresh_from_db()

        self.assertIsNone(self.reservation.hold_token)
        self.assertIsNone(self.reservation.hold_expires_at)

    def test_cancel_nonexistent_booking(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        url = reverse(
            'reserve:delete-booking',
            kwargs={'reservation_id': 99999}
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)