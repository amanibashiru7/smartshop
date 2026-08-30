from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("verify-email/", views.verify_email_view, name="verify_email"),
    path("verify-login/", views.verify_login_view, name="verify_login"),
    path("resend-otp/<str:purpose>/", views.resend_otp_view, name="resend_otp"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("application-status/", views.application_status_view, name="application_status"),
    path("staff/", views.staff_list, name="staff_list"),
    path("staff/<int:pk>/toggle/", views.staff_toggle, name="staff_toggle"),
]
