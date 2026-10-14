import re

from django.core.exceptions import ValidationError


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
