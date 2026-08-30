import json
from django.test import TestCase

from apps.accounts.models import User
from apps.shops.models import Shop
from apps.subscriptions.models import Plan, Subscription
from apps.inventory.models import Product
from .models import Sale


class POSTransactionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner@shop.com", email="owner@shop.com", password="Pass123!",
            role=User.Role.OWNER, email_verified=True,
        )
        self.shop = Shop.objects.create(name="Test Shop", owner=self.owner, address="Nairobi", status=Shop.Status.APPROVED)
        self.owner.shop = self.shop
        self.owner.save()
        plan, _ = Plan.objects.get_or_create(code=Plan.Code.FREE, defaults={"name": "Free", "max_products": 100, "max_staff": 1})
        Subscription.objects.create(shop=self.shop, plan=plan, status=Subscription.Status.ACTIVE)
        self.product = Product.objects.create(shop=self.shop, name="Soda", selling_price=100, buying_price=60, current_stock=10)
        self.client.force_login(self.owner)

    def test_sale_reduces_stock_atomically(self):
        resp = self.client.post(
            "/sales/pos/complete/",
            data=json.dumps({"items": [{"product_id": self.product.id, "quantity": 3}]}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 7)
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(float(Sale.objects.first().total_amount), 300.0)

    def test_sale_rejected_when_insufficient_stock(self):
        resp = self.client.post(
            "/sales/pos/complete/",
            data=json.dumps({"items": [{"product_id": self.product.id, "quantity": 999}]}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 10)
        self.assertEqual(Sale.objects.count(), 0)
