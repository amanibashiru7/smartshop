from django.shortcuts import render, redirect
from django.contrib import messages

from apps.core.permissions import shop_user_required, staff_permission_required, get_request_shop
from .models import Expense
from .forms import ExpenseForm


@shop_user_required
@staff_permission_required("expenses")
def expense_list(request):
    shop = get_request_shop(request)
    expenses = Expense.objects.filter(shop=shop)
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            e = form.save(commit=False)
            e.shop = shop
            e.created_by = request.user
            e.save()
            messages.success(request, "Expense recorded.")
            return redirect("expenses:expense_list")
    else:
        form = ExpenseForm()
    return render(request, "expenses/expense_list.html", {"expenses": expenses, "form": form})
