from django import forms, template

from recruitment.utils import format_vnd_number


register = template.Library()


@register.filter
def vnd(value):
    amount = format_vnd_number(value)
    return f"{amount} VNĐ" if amount else ""


@register.filter
def field_id(field, prefix=""):
    return f"{prefix}_{field.auto_id}" if prefix else field.auto_id


@register.filter
def bootstrap_field(field, prefix=""):
    widget = field.field.widget
    css_class = "form-select" if isinstance(widget, forms.Select) else "form-control"
    if isinstance(widget, forms.CheckboxInput):
        css_class = "form-check-input"
    if field.errors:
        css_class += " is-invalid"
    input_id = field_id(field, prefix)
    attrs = {"class": css_class, "id": input_id}
    descriptions = []
    if getattr(field.field, "currency", None):
        descriptions.append(f"{input_id}_currency")
    if field.help_text:
        descriptions.append(f"{input_id}_helptext")
    if field.errors:
        descriptions.append(f"{input_id}_error")
    if descriptions:
        attrs["aria-describedby"] = " ".join(descriptions)
    return field.as_widget(attrs=attrs)
