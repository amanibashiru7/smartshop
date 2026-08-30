from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

from apps.shops.models import Shop
from apps.subscriptions.models import Subscription
from apps.inventory.models import Product
from apps.sales.models import Sale
from apps.customers.models import Customer
from apps.expenses.models import Expense
from .permissions import super_admin_required, shop_user_required


@login_required
def dashboard_router(request):
    user = request.user
    if user.is_super_admin:
        return redirect("core:dashboard_superadmin")
    return redirect("core:dashboard_owner")


@super_admin_required
def dashboard_superadmin(request):
    context = {
        "total_shops": Shop.objects.count(),
        "pending": Shop.objects.filter(status=Shop.Status.PENDING).count(),
        "approved": Shop.objects.filter(status=Shop.Status.APPROVED).count(),
        "rejected": Shop.objects.filter(status=Shop.Status.REJECTED).count(),
        "suspended": Shop.objects.filter(status=Shop.Status.SUSPENDED).count(),
        "free_shops": Subscription.objects.filter(plan__code="free").count(),
        "premium_shops": Subscription.objects.filter(plan__code="premium").count(),
        "active_subs": Subscription.objects.filter(status=Subscription.Status.ACTIVE).count(),
        "expired_subs": Subscription.objects.filter(status=Subscription.Status.EXPIRED).count(),
    }
    return render(request, "core/dashboard_superadmin.html", context)


@shop_user_required
def dashboard_owner(request):
    shop = request.user.shop
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    sales_qs = Sale.objects.filter(shop=shop)
    today_sales = sales_qs.filter(created_at__date=today).aggregate(total=Sum("total_amount"))["total"] or 0
    week_sales = sales_qs.filter(created_at__date__gte=week_start).aggregate(total=Sum("total_amount"))["total"] or 0
    month_sales = sales_qs.filter(created_at__date__gte=month_start).aggregate(total=Sum("total_amount"))["total"] or 0

    products = Product.objects.filter(shop=shop, is_active=True)
    low_stock = products.filter(current_stock__lte=shop.low_stock_threshold_default)
    stock_value = sum(p.current_stock * p.buying_price for p in products)
    month_expenses = Expense.objects.filter(shop=shop, date__gte=month_start).aggregate(total=Sum("amount"))["total"] or 0

    labels, data = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime("%a"))
        data.append(float(sales_qs.filter(created_at__date=d).aggregate(total=Sum("total_amount"))["total"] or 0))

    context = {
        "today_sales": today_sales, "week_sales": week_sales, "month_sales": month_sales,
        "total_products": products.count(), "low_stock_count": low_stock.count(), "low_stock_items": low_stock[:5],
        "stock_value": stock_value, "total_customers": Customer.objects.filter(shop=shop).count(),
        "outstanding_debt": Customer.objects.filter(shop=shop).aggregate(total=Sum("balance"))["total"] or 0,
        "month_expenses": month_expenses, "estimated_profit": float(month_sales) - float(month_expenses),
        "chart_labels": labels, "chart_data": data,
    }
    return render(request, "core/dashboard_owner.html", context)


def error_403(request, exception=None):
    return render(request, "core/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "core/404.html", status=404)


def error_500(request):
    return render(request, "core/500.html", status=500)
