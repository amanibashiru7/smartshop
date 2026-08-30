from django.db import models
from django.utils import timezone
from datetime import timedelta


class Feature(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Plan(models.Model):
    class Code(models.TextChoices):
        FREE = "free", "Free"
        PREMIUM = "premium", "Premium"

    code = models.CharField(max_length=20, choices=Code.choices, unique=True)
    name = models.CharField(max_length=100)
    max_products = models.PositiveIntegerField(default=100)
    max_staff = models.PositiveIntegerField(default=1)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    features = models.ManyToManyField(Feature, blank=True, related_name="plans")

    def __str__(self):
        return self.name

    def has_feature(self, code: str) -> bool:
        return self.features.filter(code=code).exists()


class Subscription(models.Model):
    class Status(models.TextChoices):
        TRIAL = "trial", "Trial"
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    shop = models.OneToOneField("shops.Shop", on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.shop.name} - {self.plan.name} ({self.status})"

    def is_active(self) -> bool:
        if self.status not in (self.Status.ACTIVE, self.Status.TRIAL):
            return False
        if self.end_date and timezone.now() > self.end_date:
            return False
        return True

    def upgrade_to_premium(self, months=1):
        premium = Plan.objects.get(code=Plan.Code.PREMIUM)
        self.plan = premium
        self.status = self.Status.ACTIVE
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timedelta(days=30 * months)
        self.save()
