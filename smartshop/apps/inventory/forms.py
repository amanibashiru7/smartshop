from django import forms
from apps.core.formmixins import BootstrapFormMixin
from .models import Product, Category


class ProductForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "name", "sku", "barcode", "description", "buying_price",
                  "selling_price", "unit", "minimum_stock", "image", "is_active"]

    def __init__(self, *args, shop=None, **kwargs):
        super().__init__(*args, **kwargs)
        if shop:
            self.fields["category"].queryset = Category.objects.filter(shop=shop)


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class StockInForm(BootstrapFormMixin, forms.Form):
    quantity = forms.IntegerField(min_value=1)
    note = forms.CharField(max_length=255, required=False)


class StockAdjustForm(BootstrapFormMixin, forms.Form):
    new_quantity = forms.IntegerField(min_value=0)
    note = forms.CharField(max_length=255, required=True, help_text="Reason for adjustment")
