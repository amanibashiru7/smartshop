from django import forms
from apps.core.formmixins import BootstrapFormMixin


class RejectShopForm(BootstrapFormMixin, forms.Form):
    reason = forms.CharField(widget=forms.Textarea, min_length=10, label="Rejection reason")
