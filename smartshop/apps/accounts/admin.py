from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, OTP


@admin.register(User)
class SmartShopUserAdmin(UserAdmin):
    list_display = ("email", "username", "role", "staff_role", "shop", "email_verified", "is_suspended")
    list_filter = ("role", "staff_role", "is_suspended", "email_verified")
    fieldsets = UserAdmin.fieldsets + (
        ("SmartShop", {"fields": ("role", "staff_role", "shop", "phone", "email_verified", "is_suspended")}),
    )


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "created_at", "expires_at", "is_used", "attempts")
    list_filter = ("purpose", "is_used")
    readonly_fields = ("code_hash",)
