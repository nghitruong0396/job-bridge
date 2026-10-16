import re
from decimal import Decimal

from django import forms

from .utils import format_vnd_number


class VNDField(forms.DecimalField):
    currency = "VNĐ"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("min_value", 0)
        kwargs.setdefault("max_digits", 10)
        kwargs.setdefault("decimal_places", 0)
        kwargs.setdefault("help_text", "Nhập số tiền nguyên, ví dụ: 3,000,000 VNĐ.")
        kwargs.setdefault("widget", forms.TextInput(attrs={
            "inputmode": "numeric",
            "data-currency": "vnd",
            "maxlength": 13,
            "pattern": r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)",
        }))
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, (Decimal, int)):
            return format_vnd_number(value)
        return super().prepare_value(value)

    def to_python(self, value):
        if isinstance(value, str) and value.strip():
            value = value.strip()
            if not re.fullmatch(r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)", value):
                raise forms.ValidationError("Vui lòng nhập số tiền nguyên không âm, ví dụ: 3,000,000.")
            value = value.replace(",", "")
        return super().to_python(value)
