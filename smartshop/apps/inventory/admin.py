from django.contrib import admin
from .models import Category, Product, StockMovement

admin.site.register(Category)
admin.site.register(StockMovement)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "category", "current_stock", "selling_price", "is_active")
    list_filter = ("shop", "is_active")
    search_fields = ("name", "sku", "barcode")
