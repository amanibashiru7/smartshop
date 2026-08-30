from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone


class SessionIdleTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get("last_activity")
            now_ts = timezone.now().timestamp()
            timeout = settings.SESSION_IDLE_TIMEOUT_SECONDS
            if last_activity and (now_ts - last_activity) > timeout:
                logout(request)
                messages.warning(request, "Your session expired due to inactivity. Please login again.")
                return redirect("accounts:login")
            request.session["last_activity"] = now_ts
        return self.get_response(request)


class ShopStatusMiddleware:
    EXEMPT_PATH_PREFIXES = ("/accounts/", "/admin/", "/static/", "/media/", "/i18n/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and not request.path.startswith(self.EXEMPT_PATH_PREFIXES):
            if user.is_suspended:
                logout(request)
                messages.error(request, "Your account has been suspended. Contact the platform administrator.")
                return redirect("accounts:login")
            if user.shop_id and user.shop.status == user.shop.Status.SUSPENDED:
                logout(request)
                messages.error(request, "Your shop has been suspended. Contact the platform administrator.")
                return redirect("accounts:login")
        return self.get_response(request)
