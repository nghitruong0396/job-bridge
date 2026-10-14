from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


def validate_cv(file):
    FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])(file)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("CV không được vượt quá 5 MB.")
