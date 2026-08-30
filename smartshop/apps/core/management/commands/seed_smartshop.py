"""
Seeds initial data required for SmartShop to function:
- Free & Premium subscription plans with feature flags
- A Super Admin account (if one does not already exist)

Usage:
    python manage.py seed_smartshop
    python manage.py seed_smartshop --admin-email admin@smartshop.local --admin-password ChangeMe123!
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.subscriptions.models import Feature, Plan


FEATURES = [
    ("suppliers", "Supplier Management", "Manage suppliers and record purchases."),
    ("advanced_reports", "Advanced Reports", "Profit analysis, best sellers, and analytics."),
    ("pdf_export", "PDF Export", "Export reports as PDF."),
    ("excel_export", "Excel Export", "Export reports as Excel spreadsheets."),
    ("multi_branch", "Multiple Branches", "Manage more than one branch per shop."),
    ("expiry_tracking", "Expiry Date Tracking", "Track product batch expiry dates."),
]


class Command(BaseCommand):
    help = "Seed SmartShop with default plans, features, and a Super Admin account."

    def add_arguments(self, parser):
        parser.add_argument("--admin-email", default="admin@smartshop.local")
        parser.add_argument("--admin-password", default="ChangeMe123!")

    @transaction.atomic
    def handle(self, *args, **options):
        feature_objs = {}
        for code, name, desc in FEATURES:
            f, _ = Feature.objects.get_or_create(code=code, defaults={"name": name, "description": desc})
            feature_objs[code] = f
        self.stdout.write(self.style.SUCCESS(f"Ensured {len(feature_objs)} features."))

        free_plan, _ = Plan.objects.get_or_create(
            code=Plan.Code.FREE,
            defaults={"name": "Free", "max_products": 100, "max_staff": 1, "price_per_month": 0},
        )
        premium_plan, _ = Plan.objects.get_or_create(
            code=Plan.Code.PREMIUM,
            defaults={"name": "Premium", "max_products": 0, "max_staff": 0, "price_per_month": 29.99},
        )
        premium_plan.features.set(feature_objs.values())
        self.stdout.write(self.style.SUCCESS("Ensured Free and Premium plans."))

        email = options["admin_email"]
        password = options["admin_password"]
        if not User.objects.filter(role=User.Role.SUPER_ADMIN).exists():
            User.objects.create_superuser(
                username=email, email=email, password=password,
                role=User.Role.SUPER_ADMIN, email_verified=True, first_name="Super Admin",
            )
            self.stdout.write(self.style.SUCCESS(f"Created Super Admin: {email} / {password}"))
            self.stdout.write(self.style.WARNING("Change this password immediately after first login."))
        else:
            self.stdout.write(self.style.WARNING("A Super Admin already exists - skipped."))
