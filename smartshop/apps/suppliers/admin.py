from django.contrib import admin
from .models import Supplier, Purchase, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "supplier", "total_amount", "created_at")
    inlines = [PurchaseItemInline]


admin.site.register(Supplier)
