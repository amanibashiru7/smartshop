from django.shortcuts import render, redirect
from django.contrib import messages

from apps.core.permissions import shop_user_required, get_request_shop
from apps.audit.utils import log_action
from .models import Plan


@shop_user_required
def upgrade_view(request):
    shop = get_request_shop(request)
    premium = Plan.objects.filter(code=Plan.Code.PREMIUM).first()
    if request.method == "POST":
        shop.subscription.upgrade_to_premium()
        log_action(request.user, "subscription_upgraded", f"{shop.name} upgraded to Premium", shop=shop)
        messages.success(request, "Your shop has been upgraded to Premium!")
        return redirect("core:dashboard_owner")
    return render(request, "subscriptions/upgrade.html", {"premium": premium, "current": shop.subscription})
