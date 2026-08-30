from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q

from apps.core.permissions import shop_user_required, staff_permission_required, get_request_shop
from apps.subscriptions.services import within_product_limit
from apps.audit.utils import log_action
from .models import Product, Category, StockMovement
from .forms import ProductForm, CategoryForm, StockInForm, StockAdjustForm


@shop_user_required
@staff_permission_required("products_view")
def product_list(request):
    shop = get_request_shop(request)
    q = request.GET.get("q", "").strip()
    products = Product.objects.filter(shop=shop).select_related("category")
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(barcode__icontains=q))
    return render(request, "inventory/product_list.html", {"products": products, "q": q})


@shop_user_required
@staff_permission_required("products_manage")
def product_create(request):
    shop = get_request_shop(request)
    if not within_product_limit(shop, Product.objects.filter(shop=shop).count()):
        messages.error(request, "You have reached your plan's product limit. Upgrade to Premium to add more.")
        return redirect("subscriptions:upgrade")
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, shop=shop)
        if form.is_valid():
            product = form.save(commit=False)
            product.shop = shop
            product.current_stock = 0
            product.save()
            log_action(request.user, "product_created", f"Created product {product.name}", shop=shop)
            messages.success(request, "Product added successfully.")
            return redirect("inventory:product_list")
    else:
        form = ProductForm(shop=shop)
    return render(request, "inventory/product_form.html", {"form": form, "title": "Add Product"})


@shop_user_required
@staff_permission_required("products_manage")
def product_edit(request, pk):
    shop = get_request_shop(request)
    product = get_object_or_404(Product, pk=pk, shop=shop)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product, shop=shop)
        if form.is_valid():
            form.save()
            log_action(request.user, "product_updated", f"Updated product {product.name}", shop=shop)
            messages.success(request, "Product updated.")
            return redirect("inventory:product_list")
    else:
        form = ProductForm(instance=product, shop=shop)
    return render(request, "inventory/product_form.html", {"form": form, "title": "Edit Product"})


@shop_user_required
@staff_permission_required("products_manage")
def product_toggle_active(request, pk):
    shop = get_request_shop(request)
    product = get_object_or_404(Product, pk=pk, shop=shop)
    product.is_active = not product.is_active
    product.save(update_fields=["is_active"])
    messages.success(request, f"{product.name} is now {'active' if product.is_active else 'inactive'}.")
    return redirect("inventory:product_list")


@shop_user_required
@staff_permission_required("products_manage")
def category_list(request):
    shop = get_request_shop(request)
    categories = Category.objects.filter(shop=shop)
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.shop = shop
            cat.save()
            messages.success(request, "Category added.")
            return redirect("inventory:category_list")
    else:
        form = CategoryForm()
    return render(request, "inventory/category_list.html", {"categories": categories, "form": form})


@shop_user_required
@staff_permission_required("stock_view")
def stock_list(request):
    shop = get_request_shop(request)
    products = Product.objects.filter(shop=shop, is_active=True)
    return render(request, "inventory/stock_list.html", {"products": products})


@shop_user_required
@staff_permission_required("stock_in")
def stock_in(request, pk):
    shop = get_request_shop(request)
    product = get_object_or_404(Product, pk=pk, shop=shop)
    if request.method == "POST":
        form = StockInForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data["quantity"]
            with transaction.atomic():
                product = Product.objects.select_for_update().get(pk=product.pk)
                product.current_stock += qty
                product.save(update_fields=["current_stock"])
                StockMovement.objects.create(
                    shop=shop, product=product, reason=StockMovement.Reason.STOCK_IN,
                    quantity_change=qty, resulting_stock=product.current_stock,
                    note=form.cleaned_data.get("note", ""), created_by=request.user,
                )
            log_action(request.user, "stock_in", f"+{qty} to {product.name}", shop=shop)
            messages.success(request, f"Stock updated: {product.name} now has {product.current_stock} units.")
            return redirect("inventory:stock_list")
    else:
        form = StockInForm()
    return render(request, "inventory/stock_in.html", {"form": form, "product": product})


@shop_user_required
@staff_permission_required("products_manage")
def stock_adjust(request, pk):
    shop = get_request_shop(request)
    product = get_object_or_404(Product, pk=pk, shop=shop)
    if request.method == "POST":
        form = StockAdjustForm(request.POST)
        if form.is_valid():
            new_qty = form.cleaned_data["new_quantity"]
            with transaction.atomic():
                product = Product.objects.select_for_update().get(pk=product.pk)
                change = new_qty - product.current_stock
                product.current_stock = new_qty
                product.save(update_fields=["current_stock"])
                StockMovement.objects.create(
                    shop=shop, product=product, reason=StockMovement.Reason.ADJUSTMENT,
                    quantity_change=change, resulting_stock=new_qty,
                    note=form.cleaned_data["note"], created_by=request.user,
                )
            log_action(request.user, "stock_adjusted", f"{product.name} adjusted to {new_qty}", shop=shop)
            messages.success(request, "Stock adjusted.")
            return redirect("inventory:stock_list")
    else:
        form = StockAdjustForm(initial={"new_quantity": product.current_stock})
    return render(request, "inventory/stock_adjust.html", {"form": form, "product": product})


@shop_user_required
@staff_permission_required("stock_view")
def stock_history(request, pk):
    shop = get_request_shop(request)
    product = get_object_or_404(Product, pk=pk, shop=shop)
    movements = product.movements.all()[:200]
    return render(request, "inventory/stock_history.html", {"product": product, "movements": movements})
