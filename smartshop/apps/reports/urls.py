from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("sales/", views.sales_report, name="sales_report"),
    path("stock/", views.stock_report, name="stock_report"),
    path("profit/", views.profit_report, name="profit_report"),
    path("export/csv/", views.export_sales_csv, name="export_csv"),
    path("export/excel/", views.export_sales_excel, name="export_excel"),
    path("export/pdf/", views.export_sales_pdf, name="export_pdf"),
]
