class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            if "form-check-input" not in existing:
                field.widget.attrs["class"] = (existing + " form-control").strip()
