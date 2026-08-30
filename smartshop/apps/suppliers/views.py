from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from apps.core.permissions import shop_user_required, staff_permission_required, get_request_shop
from apps.subscriptions.services import has_feature
from apps.inventory.models import Product, StockMovement
from .models import Supplier, Purchase, PurchaseItem
from .forms import SupplierForm


@shop_user_required
@staff_permission_required("suppliers")
def supplier_list(request):
    shop = get_request_shop(request)
    if not has_feature(shop, "suppliers"):
        return render(request, "core/premium_required.html", {"feature": "Supplier Management"})
    suppliers = Supplier.objects.filter(shop=shop)
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.shop = shop
            s.save()
            messages.success(request, "Supplier added.")
            return redirect("suppliers:supplier_list")
    else:
        form = SupplierForm()
    return render(request, "suppliers/supplier_list.html", {"suppliers": suppliers, "form": form})


@shop_user_required
@staff_permission_required("suppliers")
def record_purchase(request, supplier_id):
    shop = get_request_shop(request)
    supplier = get_object_or_404(Supplier, pk=supplier_id, shop=shop)
    products = Product.objects.filter(shop=shop, is_active=True)
    if request.method == "POST":
        product_ids = request.POST.getlist("product_id")
        quantities = request.POST.getlist("quantity")
        unit_costs = request.POST.getlist("unit_cost")
        if not product_ids:
            messages.error(request, "Add at least one item.")
        else:
            with transaction.atomic():
                purchase = Purchase.objects.create(shop=shop, supplier=supplier, created_by=request.user)
                total = 0
                for pid, qty, cost in zip(product_ids, quantities, unit_costs):
                    product = Product.objects.select_for_update().get(pk=pid, shop=shop)
                    qty = int(qty)
                    cost = float(cost)
                    PurchaseItem.objects.create(purchase=purchase, product=product, quantity=qty, unit_cost=cost)
                    product.current_stock += qty
                    product.buying_price = cost
                    product.save(update_fields=["current_stock", "buying_price"])
                    StockMovement.objects.create(
                        shop=shop, product=product, reason=StockMovement.Reason.STOCK_IN,
                        quantity_change=qty, resulting_stock=product.current_stock,
                        note=f"Purchase #{purchase.id} from {supplier.name}", created_by=request.user,
                    )
                    total += qty * cost
                purchase.total_amount = total
                purchase.save(update_fields=["total_amount"])
                supplier.balance_owed += total
                supplier.save(update_fields=["balance_owed"])
            messages.success(request, "Purchase recorded and stock updated.")
            return redirect("suppliers:supplier_list")
    return render(request, "suppliers/record_purchase.html", {"supplier": supplier, "products": products})
