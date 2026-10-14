from django import forms

from .models import JobPost
from .validators import validate_cv


class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = (
            "title", "department", "description", "requirements",
            "number_of_positions", "bonus", "status", "deadline",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "requirements": forms.Textarea(attrs={"rows": 4}),
            "deadline": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }


class ReferralForm(forms.Form):
    full_name = forms.CharField(label="Họ tên ứng viên", max_length=150)
    email = forms.EmailField(label="Email liên hệ", required=False)
    phone = forms.CharField(label="Số điện thoại", max_length=30)
    address = forms.CharField(label="Địa chỉ", max_length=255, required=False)
    dob = forms.DateField(
        label="Ngày sinh", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    working_experience = forms.CharField(
        label="Kinh nghiệm làm việc", required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    cv = forms.FileField(
        label="CV", required=False, validators=[validate_cv],
        help_text="PDF, DOC hoặc DOCX. Tối đa 5 MB.",
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.doc,.docx"}),
    )
