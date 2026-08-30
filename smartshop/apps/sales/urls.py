from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    path("pos/", views.pos_view, name="pos"),
    path("pos/complete/", views.complete_sale, name="complete_sale"),
    path("history/", views.sale_history, name="sale_history"),
    path("<int:pk>/", views.sale_detail, name="sale_detail"),
]
