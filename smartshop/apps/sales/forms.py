from django import forms


class POSAddItemForm(forms.Form):
    product_id = forms.IntegerField()
    quantity = forms.IntegerField(min_value=1)
