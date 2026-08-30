from django.urls import path
from . import views

app_name = "subscriptions"

urlpatterns = [
    path("upgrade/", views.upgrade_view, name="upgrade"),
]
