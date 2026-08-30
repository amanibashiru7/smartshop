from django.urls import path
from . import views

app_name = "suppliers"

urlpatterns = [
    path("", views.supplier_list, name="supplier_list"),
    path("<int:supplier_id>/purchase/", views.record_purchase, name="record_purchase"),
]
