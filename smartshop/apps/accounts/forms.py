from django import forms
from django.contrib.auth.password_validation import validate_password
from apps.core.formmixins import BootstrapFormMixin
from .models import User


class RegisterForm(BootstrapFormMixin, forms.Form):
    full_name = forms.CharField(max_length=150)
    shop_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=32)
    shop_address = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        pw, cpw = cleaned.get("password"), cleaned.get("confirm_password")
        if pw and cpw and pw != cpw:
            raise forms.ValidationError("Passwords do not match.")
        if pw:
            validate_password(pw)
        return cleaned


class LoginForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class OTPForm(BootstrapFormMixin, forms.Form):
    code = forms.CharField(max_length=6, min_length=6, widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "one-time-code"}))


class ResubmitApplicationForm(BootstrapFormMixin, forms.Form):
    shop_name = forms.CharField(max_length=150)
    phone = forms.CharField(max_length=32)
    shop_address = forms.CharField(max_length=255)


class StaffCreateForm(BootstrapFormMixin, forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=32, required=False)
    staff_role = forms.ChoiceField(choices=User.StaffRole.choices)
    temporary_password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email
