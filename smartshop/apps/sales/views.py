import json
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.core.permissions import shop_user_required, staff_permission_required, get_request_shop
from apps.inventory.models import Product, StockMovement
from apps.customers.models import Customer
from apps.audit.utils import log_action
from .models import Sale, SaleItem


@shop_user_required
@staff_permission_required("pos")
def pos_view(request):
    shop = get_request_shop(request)
    products = Product.objects.filter(shop=shop, is_active=True, current_stock__gt=0)
    customers = Customer.objects.filter(shop=shop)
    return render(request, "sales/pos.html", {"products": products, "customers": customers})


@shop_user_required
@staff_permission_required("pos")
@require_POST
def complete_sale(request):
    shop = get_request_shop(request)
    try:
        payload = json.loads(request.body)
        cart = payload.get("items", [])
        customer_id = payload.get("customer_id")
        is_credit = payload.get("is_credit", False)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    if not cart:
        return JsonResponse({"error": "Cart is empty."}, status=400)

    try:
        with transaction.atomic():
            sale = Sale.objects.create(shop=shop, cashier=request.user, is_credit=is_credit,
                                        customer_id=customer_id if customer_id else None)
            total = 0
            for item in cart:
                product = Product.objects.select_for_update().get(pk=item["product_id"], shop=shop)
                qty = int(item["quantity"])
                if product.current_stock < qty:
                    raise ValueError(f"Insufficient stock for {product.name} (available: {product.current_stock}).")
                SaleItem.objects.create(sale=sale, product=product, quantity=qty, unit_price=product.selling_price)
                product.current_stock -= qty
                product.save(update_fields=["current_stock"])
                StockMovement.objects.create(
                    shop=shop, product=product, reason=StockMovement.Reason.SALE,
                    quantity_change=-qty, resulting_stock=product.current_stock,
                    note=f"Sale #{sale.id}", created_by=request.user,
                )
                total += qty * float(product.selling_price)

            sale.total_amount = total
            sale.save(update_fields=["total_amount"])

            if is_credit and sale.customer:
                sale.customer.balance += total
                sale.customer.save(update_fields=["balance"])

        log_action(request.user, "sale_completed", f"Sale #{sale.id} total {sale.total_amount}", shop=shop)
        return JsonResponse({"success": True, "sale_id": sale.id, "total": float(sale.total_amount)})
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found."}, status=404)


@shop_user_required
@staff_permission_required("sales_own")
def sale_history(request):
    shop = get_request_shop(request)
    sales = Sale.objects.filter(shop=shop).select_related("cashier", "customer")
    if request.user.is_staff_member and not request.user.has_staff_permission("sales_all"):
        sales = sales.filter(cashier=request.user)
    return render(request, "sales/sale_history.html", {"sales": sales[:200]})


@shop_user_required
@staff_permission_required("sales_own")
def sale_detail(request, pk):
    shop = get_request_shop(request)
    sale = get_object_or_404(Sale.objects.select_related("cashier", "customer"), pk=pk, shop=shop)
    return render(request, "sales/sale_detail.html", {"sale": sale, "items": sale.items.select_related("product")})
