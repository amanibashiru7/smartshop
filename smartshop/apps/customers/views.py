from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from apps.core.permissions import shop_user_required, staff_permission_required, get_request_shop
from .models import Customer, CustomerPayment
from .forms import CustomerForm, PaymentForm


@shop_user_required
@staff_permission_required("customers")
def customer_list(request):
    shop = get_request_shop(request)
    customers = Customer.objects.filter(shop=shop)
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.shop = shop
            c.save()
            messages.success(request, "Customer added.")
            return redirect("customers:customer_list")
    else:
        form = CustomerForm()
    return render(request, "customers/customer_list.html", {"customers": customers, "form": form})


@shop_user_required
@staff_permission_required("customers")
def customer_detail(request, pk):
    shop = get_request_shop(request)
    customer = get_object_or_404(Customer, pk=pk, shop=shop)
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]
            with transaction.atomic():
                customer = Customer.objects.select_for_update().get(pk=customer.pk)
                if amount > customer.balance:
                    messages.error(request, "Payment cannot exceed outstanding balance.")
                else:
                    customer.balance -= amount
                    customer.save(update_fields=["balance"])
                    CustomerPayment.objects.create(customer=customer, amount=amount,
                                                    note=form.cleaned_data.get("note", ""), received_by=request.user)
                    messages.success(request, "Payment recorded.")
            return redirect("customers:customer_detail", pk=pk)
    else:
        form = PaymentForm()
    return render(request, "customers/customer_detail.html", {
        "customer": customer, "form": form, "payments": customer.payments.all(), "sales": customer.sales.all()[:50],
    })
