import os
import requests
from django.conf import settings
from django.core.mail import send_mail

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
SENDER_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL_ADDRESS", "no-reply@smartshop.local")
SENDER_NAME = os.environ.get("DEFAULT_FROM_NAME", "SmartShop")


def _send_via_brevo_api(to_email, subject, message):
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": message,
    }
    response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=15)
    response.raise_for_status()


def send_otp_email(user, code, purpose_label):
    subject = f"SmartShop - Your {purpose_label} Code"
    message = (
        f"Hello {user.first_name or user.username},\n\n"
        f"Your SmartShop {purpose_label} code is: {code}\n"
        f"This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n"
        f"If you did not request this, please ignore this email or contact support.\n\n"
        f"- SmartShop Security"
    )
    if BREVO_API_KEY:
        _send_via_brevo_api(user.email, subject, message)
    else:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


def send_notification_email(user, subject, message):
    full_subject = f"SmartShop - {subject}"
    if BREVO_API_KEY:
        try:
            _send_via_brevo_api(user.email, full_subject, message)
        except Exception:
            pass
    else:
        send_mail(full_subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
