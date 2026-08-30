from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard_router, name="dashboard_router"),
    path("dashboard/super-admin/", views.dashboard_superadmin, name="dashboard_superadmin"),
    path("dashboard/", views.dashboard_owner, name="dashboard_owner"),
]
