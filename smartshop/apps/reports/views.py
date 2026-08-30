import csv
from datetime import datetime, timedelta

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, Count
from django.utils import timezone

from apps.core.permissions import shop_user_required, staff_permission_required, get_request_shop
from apps.subscriptions.services import has_feature
from apps.sales.models import Sale, SaleItem
from apps.inventory.models import Product
from apps.expenses.models import Expense


def _date_range(request):
    today = timezone.now().date()
    start = request.GET.get("start")
    end = request.GET.get("end")
    if start and end:
        try:
            start = datetime.strptime(start, "%Y-%m-%d").date()
            end = datetime.strptime(end, "%Y-%m-%d").date()
            return start, end
        except ValueError:
            pass
    return today - timedelta(days=30), today


@shop_user_required
@staff_permission_required("reports")
def sales_report(request):
    shop = get_request_shop(request)
    start, end = _date_range(request)
    sales = Sale.objects.filter(shop=shop, created_at__date__gte=start, created_at__date__lte=end)
    summary = sales.aggregate(total=Sum("total_amount"), count=Count("id"))
    daily = (
        sales.extra(select={"day": "date(created_at)"}).values("day")
        .annotate(total=Sum("total_amount")).order_by("day")
    )
    context = {"start": start, "end": end, "summary": summary, "daily": daily, "sales": sales.order_by("-created_at")[:100]}
    return render(request, "reports/sales_report.html", context)


@shop_user_required
@staff_permission_required("reports")
def stock_report(request):
    shop = get_request_shop(request)
    products = Product.objects.filter(shop=shop)
    stock_value = sum(p.current_stock * p.buying_price for p in products)
    return render(request, "reports/stock_report.html", {"products": products, "stock_value": stock_value})


@shop_user_required
@staff_permission_required("reports")
def profit_report(request):
    shop = get_request_shop(request)
    if not has_feature(shop, "advanced_reports"):
        return render(request, "core/premium_required.html", {"feature": "Profit & Advanced Analytics"})
    start, end = _date_range(request)
    items = SaleItem.objects.filter(sale__shop=shop, sale__created_at__date__gte=start, sale__created_at__date__lte=end)
    revenue = sum(i.line_total for i in items)
    cost = sum(i.quantity * i.product.buying_price for i in items)
    expenses = Expense.objects.filter(shop=shop, date__gte=start, date__lte=end).aggregate(t=Sum("amount"))["t"] or 0

    best_sellers = (
        items.values("product__name").annotate(qty=Sum("quantity"), revenue=Sum("unit_price"))
        .order_by("-qty")[:10]
    )
    context = {
        "start": start, "end": end, "revenue": revenue, "cost": cost, "expenses": expenses,
        "profit": float(revenue) - float(cost) - float(expenses), "best_sellers": best_sellers,
    }
    return render(request, "reports/profit_report.html", context)


@shop_user_required
@staff_permission_required("reports")
def export_sales_csv(request):
    shop = get_request_shop(request)
    start, end = _date_range(request)
    sales = Sale.objects.filter(shop=shop, created_at__date__gte=start, created_at__date__lte=end)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="sales_{start}_{end}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Sale ID", "Date", "Cashier", "Customer", "Total", "Credit"])
    for s in sales:
        writer.writerow([s.id, s.created_at.strftime("%Y-%m-%d %H:%M"), s.cashier.email,
                          s.customer.name if s.customer else "", s.total_amount, s.is_credit])
    return response


@shop_user_required
@staff_permission_required("reports")
def export_sales_excel(request):
    shop = get_request_shop(request)
    if not has_feature(shop, "excel_export"):
        return render(request, "core/premium_required.html", {"feature": "Excel Export"})
    from openpyxl import Workbook
    start, end = _date_range(request)
    sales = Sale.objects.filter(shop=shop, created_at__date__gte=start, created_at__date__lte=end)

    wb = Workbook()
    ws = wb.active
    ws.title = "Sales"
    ws.append(["Sale ID", "Date", "Cashier", "Customer", "Total", "Credit"])
    for s in sales:
        ws.append([s.id, s.created_at.strftime("%Y-%m-%d %H:%M"), s.cashier.email,
                   s.customer.name if s.customer else "", float(s.total_amount), s.is_credit])
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="sales_{start}_{end}.xlsx"'
    wb.save(response)
    return response


@shop_user_required
@staff_permission_required("reports")
def export_sales_pdf(request):
    shop = get_request_shop(request)
    if not has_feature(shop, "pdf_export"):
        return render(request, "core/premium_required.html", {"feature": "PDF Export"})
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from io import BytesIO

    start, end = _date_range(request)
    sales = Sale.objects.filter(shop=shop, created_at__date__gte=start, created_at__date__lte=end)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"{shop.name} - Sales Report ({start} to {end})", styles["Title"])]
    data = [["Sale ID", "Date", "Cashier", "Total"]]
    for s in sales:
        data.append([str(s.id), s.created_at.strftime("%Y-%m-%d"), s.cashier.email, str(s.total_amount)])
    table = Table(data)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="sales_{start}_{end}.pdf"'
    return response
