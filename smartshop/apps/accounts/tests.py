from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from .models import User, OTP
from apps.shops.models import Shop


class OTPTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="a@b.com", email="a@b.com", password="Testpass123!")

    def test_otp_correct_code_verifies(self):
        otp, code = OTP.issue(self.user, OTP.Purpose.EMAIL_VERIFY)
        self.assertTrue(otp.verify(code))

    def test_otp_wrong_code_fails(self):
        otp, code = OTP.issue(self.user, OTP.Purpose.EMAIL_VERIFY)
        self.assertFalse(otp.verify("000000"))

    def test_otp_cannot_be_reused(self):
        otp, code = OTP.issue(self.user, OTP.Purpose.EMAIL_VERIFY)
        self.assertTrue(otp.verify(code))
        self.assertFalse(otp.verify(code))

    def test_otp_expired_fails(self):
        otp, code = OTP.issue(self.user, OTP.Purpose.EMAIL_VERIFY)
        otp.expires_at = timezone.now() - timedelta(minutes=1)
        otp.save()
        self.assertFalse(otp.verify(code))

    def test_otp_max_attempts_locks(self):
        otp, code = OTP.issue(self.user, OTP.Purpose.EMAIL_VERIFY)
        for _ in range(6):
            otp.verify("000000")
        self.assertFalse(otp.verify(code))


class RegistrationFlowTests(TestCase):
    def test_register_creates_pending_shop(self):
        resp = self.client.post("/accounts/register/", {
            "full_name": "Jane Doe", "shop_name": "Jane's Shop", "email": "jane@example.com",
            "phone": "0700000000", "shop_address": "Nairobi", "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        })
        self.assertEqual(resp.status_code, 302)
        shop = Shop.objects.get(name="Jane's Shop")
        self.assertEqual(shop.status, Shop.Status.PENDING)
        self.assertFalse(shop.owner.email_verified)
