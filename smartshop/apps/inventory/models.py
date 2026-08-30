from django.db import models
from django.conf import settings


class Category(models.Model):
    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("shop", "name")
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=64, blank=True)
    barcode = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    buying_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=32, default="pcs")
    current_stock = models.IntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("shop", "name")
        indexes = [models.Index(fields=["shop", "is_active"])]

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock


class StockMovement(models.Model):
    class Reason(models.TextChoices):
        STOCK_IN = "stock_in", "Stock In (Purchase)"
        SALE = "sale", "Sale"
        ADJUSTMENT = "adjustment", "Manual Adjustment"
        RETURN = "return", "Return"

    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="stock_movements")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="movements")
    reason = models.CharField(max_length=20, choices=Reason.choices)
    quantity_change = models.IntegerField(help_text="Positive to add, negative to remove")
    resulting_stock = models.IntegerField()
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
