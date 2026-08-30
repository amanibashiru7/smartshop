from django.db import models
from django.conf import settings


class Expense(models.Model):
    class Category(models.TextChoices):
        RENT = "rent", "Rent"
        ELECTRICITY = "electricity", "Electricity"
        TRANSPORT = "transport", "Transport"
        SALARIES = "salaries", "Salaries"
        MAINTENANCE = "maintenance", "Maintenance"
        OTHER = "other", "Other"

    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="expenses")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
