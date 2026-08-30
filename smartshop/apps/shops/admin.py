from django.contrib import admin
from .models import Shop, ShopApplicationHistory


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "created_at")
    list_filter = ("status",)


admin.site.register(ShopApplicationHistory)
