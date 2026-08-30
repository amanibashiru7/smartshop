from django.test import TestCase

from apps.accounts.models import User
from apps.inventory.models import Product
from .models import Shop


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.owner_a = User.objects.create_user(username="a@shop.com", email="a@shop.com", password="Pass123!", role=User.Role.OWNER, email_verified=True)
        self.shop_a = Shop.objects.create(name="Shop A", owner=self.owner_a, address="Nairobi", status=Shop.Status.APPROVED)
        self.owner_a.shop = self.shop_a
        self.owner_a.save()

        self.owner_b = User.objects.create_user(username="b@shop.com", email="b@shop.com", password="Pass123!", role=User.Role.OWNER, email_verified=True)
        self.shop_b = Shop.objects.create(name="Shop B", owner=self.owner_b, address="Nairobi", status=Shop.Status.APPROVED)
        self.owner_b.shop = self.shop_b
        self.owner_b.save()

        self.product_a = Product.objects.create(shop=self.shop_a, name="Shop A Product", selling_price=50)

    def test_owner_b_cannot_edit_shop_a_product(self):
        self.client.force_login(self.owner_b)
        resp = self.client.get(f"/inventory/products/{self.product_a.id}/edit/")
        self.assertEqual(resp.status_code, 404)  # get_object_or_404 with shop filter
