from apps.subscriptions.services import get_active_plan


def shop_context(request):
    ctx = {}
    user = getattr(request, "user", None)
    if user and user.is_authenticated and user.shop_id:
        ctx["current_shop"] = user.shop
        ctx["current_plan"] = get_active_plan(user.shop)
    return ctx
