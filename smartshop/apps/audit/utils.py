def log_action(user, action, description="", shop=None, request=None):
    from .models import AuditLog
    ip = None
    if request is not None:
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")
    AuditLog.objects.create(user=user, shop=shop or getattr(user, "shop", None), action=action, description=description, ip_address=ip)
