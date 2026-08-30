from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def super_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_super_admin:
            messages.error(request, "You do not have permission to access that page.")
            return redirect("accounts:login")
        return view_func(request, *args, **kwargs)
    return wrapper


def shop_user_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.is_super_admin or not user.shop_id:
            messages.error(request, "You do not have permission to access that page.")
            return redirect("accounts:login")
        if user.shop.status != user.shop.Status.APPROVED:
            messages.error(request, "Your shop is not active yet.")
            return redirect("accounts:login")
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_permission_required(module):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated or not user.shop_id:
                messages.error(request, "You do not have permission to access that page.")
                return redirect("accounts:login")
            if not user.has_staff_permission(module):
                messages.error(request, "You do not have permission to perform this action.")
                return redirect("core:dashboard_router")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_request_shop(request):
    """NEVER trust a shop_id submitted by the browser (spec section 3) - always derive from session user."""
    return request.user.shop
