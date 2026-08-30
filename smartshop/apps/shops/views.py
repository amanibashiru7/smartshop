from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from apps.core.permissions import super_admin_required
from apps.audit.utils import log_action
from apps.accounts.utils import send_notification_email
from apps.subscriptions.models import Plan, Subscription
from .models import Shop, ShopApplicationHistory
from .forms import RejectShopForm


@super_admin_required
def pending_applications(request):
    shops = Shop.objects.filter(status=Shop.Status.PENDING).select_related("owner").order_by("created_at")
    return render(request, "shops/pending_applications.html", {"shops": shops})


@super_admin_required
def all_shops(request):
    shops = Shop.objects.select_related("owner", "subscription", "subscription__plan").order_by("-created_at")
    return render(request, "shops/all_shops.html", {"shops": shops})


@super_admin_required
def approve_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    shop.status = Shop.Status.APPROVED
    shop.approved_at = timezone.now()
    shop.save()
    ShopApplicationHistory.objects.create(shop=shop, status=Shop.Status.APPROVED, note="Approved by Super Admin.", actor=request.user)

    free_plan, _ = Plan.objects.get_or_create(code=Plan.Code.FREE, defaults={"name": "Free", "max_products": 100, "max_staff": 1})
    Subscription.objects.get_or_create(shop=shop, defaults={"plan": free_plan, "status": Subscription.Status.ACTIVE})

    send_notification_email(shop.owner, "Shop Approved", f"Congratulations! {shop.name} has been approved. You can now login.")
    log_action(request.user, "shop_approved", f"Approved shop {shop.name}", shop=shop)
    messages.success(request, f"{shop.name} has been approved.")
    return redirect("shops:pending_applications")


@super_admin_required
def reject_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    if request.method == "POST":
        form = RejectShopForm(request.POST)
        if form.is_valid():
            shop.status = Shop.Status.REJECTED
            shop.rejection_reason = form.cleaned_data["reason"]
            shop.save()
            ShopApplicationHistory.objects.create(shop=shop, status=Shop.Status.REJECTED, note=form.cleaned_data["reason"], actor=request.user)
            send_notification_email(shop.owner, "Application Rejected", f"Your application was rejected: {form.cleaned_data['reason']}")
            log_action(request.user, "shop_rejected", f"Rejected shop {shop.name}", shop=shop)
            messages.success(request, f"{shop.name} application rejected.")
            return redirect("shops:pending_applications")
    else:
        form = RejectShopForm()
    return render(request, "shops/reject_shop.html", {"shop": shop, "form": form})


@super_admin_required
def suspend_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    shop.status = Shop.Status.SUSPENDED
    shop.save()
    ShopApplicationHistory.objects.create(shop=shop, status=Shop.Status.SUSPENDED, note="Suspended by Super Admin.", actor=request.user)
    send_notification_email(shop.owner, "Account Suspended", "Your shop account has been suspended. Contact support.")
    log_action(request.user, "shop_suspended", f"Suspended shop {shop.name}", shop=shop)
    messages.success(request, f"{shop.name} has been suspended.")
    return redirect("shops:all_shops")


@super_admin_required
def reactivate_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    shop.status = Shop.Status.APPROVED
    shop.save()
    ShopApplicationHistory.objects.create(shop=shop, status=Shop.Status.APPROVED, note="Reactivated by Super Admin.", actor=request.user)
    log_action(request.user, "shop_reactivated", f"Reactivated shop {shop.name}", shop=shop)
    messages.success(request, f"{shop.name} has been reactivated.")
    return redirect("shops:all_shops")
