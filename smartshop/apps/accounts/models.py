import secrets
import hashlib
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        OWNER = "owner", "Shop Owner"
        STAFF = "staff", "Shop Staff"

    class StaffRole(models.TextChoices):
        CASHIER = "cashier", "Cashier"
        STORE_KEEPER = "store_keeper", "Store Keeper"
        MANAGER = "manager", "Manager"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OWNER)
    staff_role = models.CharField(max_length=20, choices=StaffRole.choices, blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True)
    shop = models.ForeignKey("shops.Shop", null=True, blank=True, on_delete=models.CASCADE, related_name="members")
    email_verified = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF

    def has_staff_permission(self, module: str) -> bool:
        if self.is_owner or self.is_super_admin:
            return True
        if not self.is_staff_member:
            return False
        perms = STAFF_ROLE_PERMISSIONS.get(self.staff_role, set())
        return module in perms


STAFF_ROLE_PERMISSIONS = {
    User.StaffRole.CASHIER: {"pos", "sales_own"},
    User.StaffRole.STORE_KEEPER: {"products_view", "stock_in", "stock_view"},
    User.StaffRole.MANAGER: {
        "pos", "sales_own", "sales_all", "products_view", "products_manage",
        "stock_in", "stock_view", "customers", "suppliers", "expenses", "reports",
    },
}


def generate_otp_code(length=None):
    length = length or settings.OTP_LENGTH
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


class OTP(models.Model):
    class Purpose(models.TextChoices):
        EMAIL_VERIFY = "email_verify", "Email Verification"
        LOGIN = "login", "Login Verification"
        PASSWORD_RESET = "password_reset", "Password Reset"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otps")
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    code_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["user", "purpose", "is_used"])]

    @classmethod
    def issue(cls, user, purpose):
        cls.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
        code = generate_otp_code()
        otp = cls.objects.create(
            user=user, purpose=purpose, code_hash=hash_otp(code),
            expires_at=timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
        )
        return otp, code

    def is_expired(self):
        return timezone.now() > self.expires_at

    def verify(self, code: str) -> bool:
        if self.is_used or self.is_expired():
            return False
        if self.attempts >= settings.OTP_MAX_ATTEMPTS:
            return False
        self.attempts += 1
        ok = secrets.compare_digest(self.code_hash, hash_otp(code))
        if ok:
            self.is_used = True
        self.save(update_fields=["attempts", "is_used"])
        return ok
