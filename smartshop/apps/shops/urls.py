from django.urls import path
from . import views

app_name = "shops"

urlpatterns = [
    path("pending/", views.pending_applications, name="pending_applications"),
    path("all/", views.all_shops, name="all_shops"),
    path("<int:shop_id>/approve/", views.approve_shop, name="approve_shop"),
    path("<int:shop_id>/reject/", views.reject_shop, name="reject_shop"),
    path("<int:shop_id>/suspend/", views.suspend_shop, name="suspend_shop"),
    path("<int:shop_id>/reactivate/", views.reactivate_shop, name="reactivate_shop"),
]
