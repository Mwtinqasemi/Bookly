from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction

from account.models import Profile


class ProfileModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='StrongPass123!'
        )

    def test_create_profile(self):
        profile = Profile.objects.create(
            user=self.user,
            phone='09123456789'
        )

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone, '09123456789')

    def test_profile_string_representation(self):
        profile = Profile.objects.create(
            user=self.user,
            phone='09123456789'
        )

        self.assertEqual(str(profile), 'testuser')

    def test_profile_phone_must_be_unique(self):
        Profile.objects.create(
            user=self.user,
            phone='09123456789'
        )

        another_user = User.objects.create_user(
            username='anotheruser',
            password='StrongPass123!'
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Profile.objects.create(
                    user=another_user,
                    phone='09123456789'
                )

    def test_user_can_have_only_one_profile(self):
        Profile.objects.create(
            user=self.user,
            phone='09123456789'
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Profile.objects.create(
                    user=self.user,
                    phone='09987654321'
                )

    def test_deleting_user_deletes_profile(self):
        profile = Profile.objects.create(
            user=self.user,
            phone='09123456789'
        )

        self.user.delete()

        self.assertFalse(
            Profile.objects.filter(id=profile.id).exists()
        )
