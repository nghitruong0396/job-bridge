import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError


def format_vnd_number(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite():
            return ""
        amount = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"{amount:,}"
    except (InvalidOperation, ValueError, TypeError):
        return ""


def normalize_phone(phone):
    if not isinstance(phone, str):
        raise ValidationError("Số điện thoại không hợp lệ.")

    phone = re.sub(r"[\s().-]", "", phone)
    if phone.startswith("+84"):
        national_number = phone[3:]
    elif phone.startswith("0084"):
        national_number = phone[4:]
    elif phone.startswith("84"):
        national_number = phone[2:]
    elif phone.startswith("0"):
        national_number = phone[1:]
    else:
        raise ValidationError("Vui lòng nhập số điện thoại Việt Nam hợp lệ.")

    if not re.fullmatch(r"(?:[35789][0-9]{8}|2[0-9]{9})", national_number):
        raise ValidationError("Vui lòng nhập số điện thoại Việt Nam hợp lệ.")

    return f"+84{national_number}"
