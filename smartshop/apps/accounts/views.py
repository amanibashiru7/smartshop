from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db import transaction

from .forms import RegisterForm, LoginForm, OTPForm, ResubmitApplicationForm, StaffCreateForm
from .models import User, OTP
from .utils import send_otp_email, send_notification_email
from apps.shops.models import Shop, ShopApplicationHistory
from apps.audit.utils import log_action
from apps.core.permissions import shop_user_required, get_request_shop
from apps.subscriptions.services import within_staff_limit


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data["email"], email=data["email"], password=data["password"],
                    first_name=data["full_name"], phone=data["phone"], role=User.Role.OWNER, is_active=True,
                )
                shop = Shop.objects.create(
                    name=data["shop_name"], owner=user, address=data["shop_address"],
                    email=data["email"], phone=data["phone"], status=Shop.Status.PENDING,
                )
                user.shop = shop
                user.save(update_fields=["shop"])
                ShopApplicationHistory.objects.create(shop=shop, status=Shop.Status.PENDING, note="Application submitted.")

            otp, code = OTP.issue(user, OTP.Purpose.EMAIL_VERIFY)
            send_otp_email(user, code, "Email Verification")
            request.session["pending_verify_user_id"] = user.id
            messages.success(request, "Account created. Enter the verification code sent to your email.")
            return redirect("accounts:verify_email")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def verify_email_view(request):
    user_id = request.session.get("pending_verify_user_id")
    if not user_id:
        return redirect("accounts:register")
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            otp = OTP.objects.filter(user=user, purpose=OTP.Purpose.EMAIL_VERIFY, is_used=False).order_by("-created_at").first()
            if otp and otp.verify(form.cleaned_data["code"]):
                user.email_verified = True
                user.save(update_fields=["email_verified"])
                del request.session["pending_verify_user_id"]
                messages.success(request, "Email verified! Your shop application is now pending Super Admin approval.")
                return redirect("accounts:login")
            messages.error(request, "Invalid or expired code.")
    else:
        form = OTPForm()
    return render(request, "accounts/verify_email.html", {"form": form, "email": user.email})


def resend_otp_view(request, purpose):
    user_id = request.session.get("pending_verify_user_id") or request.session.get("pending_login_user_id")
    if not user_id:
        return redirect("accounts:login")
    user = get_object_or_404(User, id=user_id)
    last_otp = OTP.objects.filter(user=user, purpose=purpose).order_by("-created_at").first()
    if last_otp and (timezone.now() - last_otp.created_at).total_seconds() < 60:
        messages.error(request, "Please wait 60 seconds before requesting another code.")
    else:
        otp, code = OTP.issue(user, purpose)
        send_otp_email(user, code, "Verification")
        messages.success(request, "A new verification code has been sent to your email.")
    redirect_name = "accounts:verify_email" if purpose == OTP.Purpose.EMAIL_VERIFY else "accounts:verify_login"
    return redirect(redirect_name)


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower().strip()
            password = form.cleaned_data["password"]
            user = authenticate(request, username=email, password=password)
            if user is None:
                messages.error(request, "Invalid email or password.")
                return render(request, "accounts/login.html", {"form": form})
            if user.is_suspended:
                messages.error(request, "Your account has been suspended.")
                return render(request, "accounts/login.html", {"form": form})
            if not user.email_verified:
                request.session["pending_verify_user_id"] = user.id
                messages.warning(request, "Please verify your email first.")
                return redirect("accounts:verify_email")
            effective_shop = user.shop
            if effective_shop and effective_shop.status != Shop.Status.APPROVED:
                request.session["pending_status_user_id"] = user.id
                return redirect("accounts:application_status")

            otp, code = OTP.issue(user, OTP.Purpose.LOGIN)
            send_otp_email(user, code, "Login Verification")
            request.session["pending_login_user_id"] = user.id
            return redirect("accounts:verify_login")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def verify_login_view(request):
    user_id = request.session.get("pending_login_user_id")
    if not user_id:
        return redirect("accounts:login")
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            otp = OTP.objects.filter(user=user, purpose=OTP.Purpose.LOGIN, is_used=False).order_by("-created_at").first()
            if otp and otp.verify(form.cleaned_data["code"]):
                login(request, user)
                user.last_activity = timezone.now()
                user.save(update_fields=["last_activity"])
                del request.session["pending_login_user_id"]
                request.session["last_activity"] = timezone.now().timestamp()
                log_action(user, "login", f"{user.email} logged in", shop=user.shop)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect("core:dashboard_router")
            messages.error(request, "Invalid or expired code.")
    else:
        form = OTPForm()
    return render(request, "accounts/verify_login.html", {"form": form, "email": user.email})


def application_status_view(request):
    user_id = request.session.get("pending_status_user_id")
    if not user_id:
        return redirect("accounts:login")
    user = get_object_or_404(User, id=user_id)
    shop = user.shop

    if request.method == "POST" and shop.status == Shop.Status.REJECTED:
        form = ResubmitApplicationForm(request.POST)
        if form.is_valid():
            shop.name = form.cleaned_data["shop_name"]
            shop.phone = form.cleaned_data["phone"]
            shop.address = form.cleaned_data["shop_address"]
            shop.status = Shop.Status.PENDING
            shop.rejection_reason = ""
            shop.save()
            ShopApplicationHistory.objects.create(shop=shop, status=Shop.Status.PENDING, note="Resubmitted by owner.")
            messages.success(request, "Application resubmitted. Awaiting Super Admin review.")
            return redirect("accounts:login")
    else:
        form = ResubmitApplicationForm(initial={"shop_name": shop.name, "phone": shop.phone, "shop_address": shop.address})
    return render(request, "accounts/application_status.html", {"shop": shop, "form": form})


@login_required
def logout_view(request):
    log_action(request.user, "logout", f"{request.user.email} logged out", shop=request.user.shop)
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


@shop_user_required
def staff_list(request):
    shop = get_request_shop(request)
    if not request.user.is_owner:
        messages.error(request, "Only the shop owner can manage staff.")
        return redirect("core:dashboard_router")
    staff = User.objects.filter(shop=shop, role=User.Role.STAFF)

    if request.method == "POST":
        form = StaffCreateForm(request.POST)
        if not within_staff_limit(shop, staff.count()):
            messages.error(request, "You have reached your plan's staff limit. Upgrade to Premium to add more staff.")
        elif form.is_valid():
            data = form.cleaned_data
            member = User.objects.create_user(
                username=data["email"], email=data["email"], password=data["temporary_password"],
                first_name=data["full_name"], phone=data.get("phone", ""),
                role=User.Role.STAFF, staff_role=data["staff_role"], shop=shop,
                email_verified=True, is_active=True,
            )
            send_notification_email(member, "Your SmartShop Staff Account",
                                     f"You've been added as {member.get_staff_role_display()} at {shop.name}. "
                                     f"Login with email {member.email} and the temporary password provided by your manager.")
            log_action(request.user, "staff_created", f"Added staff {member.email}", shop=shop)
            messages.success(request, "Staff account created.")
            return redirect("accounts:staff_list")
    else:
        form = StaffCreateForm()
    return render(request, "accounts/staff_list.html", {"staff": staff, "form": form})


@shop_user_required
def staff_toggle(request, pk):
    shop = get_request_shop(request)
    if not request.user.is_owner:
        messages.error(request, "Only the shop owner can manage staff.")
        return redirect("core:dashboard_router")
    member = get_object_or_404(User, pk=pk, shop=shop, role=User.Role.STAFF)
    member.is_suspended = not member.is_suspended
    member.save(update_fields=["is_suspended"])
    messages.success(request, f"{member.email} is now {'suspended' if member.is_suspended else 'active'}.")
    return redirect("accounts:staff_list")
