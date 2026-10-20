from django import forms

from .models import Application, Candidate, JobPost
from .utils import normalize_phone
from .validators import validate_cv


class JobPostForm(forms.ModelForm):
    bonus = forms.IntegerField(
        label="Thưởng giới thiệu (VNĐ)", min_value=0, max_value=9999999999,
        help_text="Nhập số tiền nguyên, ví dụ: 3000000.",
    )

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
        label="CV", required=True, validators=[validate_cv],
        help_text="PDF, DOC hoặc DOCX. Tối đa 5 MB.",
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.doc,.docx"}),
    )

    def clean_phone(self):
        return normalize_phone(self.cleaned_data["phone"])


class CandidateForm(forms.ModelForm):
    def clean_phone(self):
        return normalize_phone(self.cleaned_data["phone"])

    class Meta:
        model = Candidate
        fields = (
            "full_name", "email", "phone", "address", "dob",
            "working_experience", "note",
        )
        widgets = {
            "dob": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "working_experience": forms.Textarea(attrs={"rows": 4}),
            "note": forms.Textarea(attrs={"rows": 4}),
        }


class ApplicationStageForm(forms.Form):
    to_stage = forms.ChoiceField(label="Trạng thái tiếp theo")
    note = forms.CharField(
        label="Ghi chú nội bộ", required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, application, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = dict(Application.Stage.choices)
        self.fields["to_stage"].choices = [
            (stage, labels[stage])
            for stage in Application.ALLOWED_TRANSITIONS.get(application.current_stage, ())
        ]


class ApplicationNoteForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ("note",)
        widgets = {"note": forms.Textarea(attrs={"rows": 3})}
