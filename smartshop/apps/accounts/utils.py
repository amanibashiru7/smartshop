from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(user, code, purpose_label):
    subject = f"SmartShop - Your {purpose_label} Code"
    message = (
        f"Hello {user.first_name or user.username},\n\n"
        f"Your SmartShop {purpose_label} code is: {code}\n"
        f"This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n"
        f"If you did not request this, please ignore this email or contact support.\n\n"
        f"- SmartShop Security"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


def send_notification_email(user, subject, message):
    send_mail(f"SmartShop - {subject}", message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
