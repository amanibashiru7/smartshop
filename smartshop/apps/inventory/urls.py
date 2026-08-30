from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/toggle/", views.product_toggle_active, name="product_toggle_active"),
    path("categories/", views.category_list, name="category_list"),
    path("stock/", views.stock_list, name="stock_list"),
    path("stock/<int:pk>/in/", views.stock_in, name="stock_in"),
    path("stock/<int:pk>/adjust/", views.stock_adjust, name="stock_adjust"),
    path("stock/<int:pk>/history/", views.stock_history, name="stock_history"),
]
