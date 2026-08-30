def has_feature(shop, feature_code: str) -> bool:
    if shop is None:
        return False
    try:
        sub = shop.subscription
    except Exception:
        return False
    if not sub.is_active():
        return False
    return sub.plan.has_feature(feature_code)


def get_active_plan(shop):
    try:
        sub = shop.subscription
    except Exception:
        return None
    return sub.plan if sub.is_active() else None


def within_product_limit(shop, current_count: int) -> bool:
    plan = get_active_plan(shop)
    if plan is None:
        return False
    if plan.max_products == 0:
        return True
    return current_count < plan.max_products


def within_staff_limit(shop, current_count: int) -> bool:
    plan = get_active_plan(shop)
    if plan is None:
        return False
    if plan.max_staff == 0:
        return True
    return current_count < plan.max_staff
