from django.contrib import admin
from .models import Feature, Plan, Subscription

admin.site.register(Feature)
admin.site.register(Plan)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("shop", "plan", "status", "start_date", "end_date")
    list_filter = ("status", "plan")
