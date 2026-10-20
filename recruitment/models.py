from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction

from accounts.models import User

from .utils import normalize_phone
from .validators import validate_cv


class JobPost(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Bản nháp"
        OPEN = "OPEN", "Đang mở"
        CLOSED = "CLOSED", "Đã đóng"

    title = models.CharField("Vị trí", max_length=200)
    department = models.CharField("Bộ phận tuyển dụng", max_length=150)
    description = models.TextField("Mô tả công việc")
    requirements = models.TextField("Yêu cầu ứng viên")
    number_of_positions = models.PositiveIntegerField(
        "Số lượng tuyển", default=1, validators=[MinValueValidator(1)]
    )
    bonus = models.DecimalField(
        "Thưởng giới thiệu",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(
        "Trạng thái", max_length=6, choices=Status.choices, default=Status.DRAFT
    )
    deadline = models.DateField("Hạn nhận hồ sơ")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_jobs",
        verbose_name="Người tạo",
    )
    created_at = models.DateTimeField("Thời gian tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Thời gian cập nhật", auto_now=True)
    is_deleted = models.BooleanField("Đã xóa", default=False)

    class Meta:
        verbose_name = "Tin tuyển dụng"
        verbose_name_plural = "Tin tuyển dụng"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(number_of_positions__gt=0),
                name="job_positions_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(bonus__gte=0),
                name="job_bonus_nonnegative",
            ),
        ]

    def __str__(self):
        return self.title


class Candidate(models.Model):
    full_name = models.CharField("Họ tên", max_length=150)
    email = models.EmailField("Email liên hệ", blank=True)
    phone = models.CharField("Số điện thoại", max_length=20, unique=True)
    address = models.CharField("Địa chỉ", max_length=255, blank=True)
    dob = models.DateField("Ngày sinh", blank=True, null=True)
    working_experience = models.TextField("Kinh nghiệm làm việc", blank=True)
    note = models.TextField("Ghi chú nội bộ", blank=True)
    created_at = models.DateTimeField("Thời gian tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Thời gian cập nhật", auto_now=True)

    class Meta:
        verbose_name = "Ứng viên"
        verbose_name_plural = "Ứng viên"
        ordering = ["full_name", "id"]

    def clean(self):
        super().clean()
        self.phone = normalize_phone(self.phone)

    def save(self, *args, **kwargs):
        self.phone = normalize_phone(self.phone)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.phone}"


class Application(models.Model):
    class Stage(models.TextChoices):
        APPLIED = "APPLIED", "Đã giới thiệu"
        SCREENING = "SCREENING", "Sàng lọc"
        INTERVIEW = "INTERVIEW", "Phỏng vấn"
        HIRED = "HIRED", "Đã tuyển"
        FAILED = "FAILED", "Không tuyển"

    ALLOWED_TRANSITIONS = {
        Stage.APPLIED: (Stage.SCREENING, Stage.FAILED),
        Stage.SCREENING: (Stage.INTERVIEW, Stage.FAILED),
        Stage.INTERVIEW: (Stage.HIRED, Stage.FAILED),
        Stage.HIRED: (),
        Stage.FAILED: (),
    }

    job = models.ForeignKey(
        JobPost,
        on_delete=models.PROTECT,
        related_name="applications",
        verbose_name="Tin tuyển dụng",
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.PROTECT,
        related_name="applications",
        verbose_name="Ứng viên",
    )
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="referred_applications",
        verbose_name="Người giới thiệu",
    )
    cv = models.FileField(
        "CV", upload_to="cvs/%Y/%m/", blank=True, validators=[validate_cv]
    )
    current_stage = models.CharField(
        "Trạng thái tuyển dụng",
        max_length=9,
        choices=Stage.choices,
        default=Stage.APPLIED,
    )
    bonus_amount = models.DecimalField(
        "Mức thưởng lúc giới thiệu",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    note = models.TextField("Ghi chú nội bộ", blank=True)
    applied_at = models.DateTimeField("Thời gian giới thiệu", auto_now_add=True)
    updated_at = models.DateTimeField("Thời gian cập nhật", auto_now=True)

    class Meta:
        verbose_name = "Hồ sơ giới thiệu"
        verbose_name_plural = "Hồ sơ giới thiệu"
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job"], name="application_candidate_job_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(bonus_amount__gte=0),
                name="application_bonus_nonnegative",
            ),
        ]

    def change_stage(self, to_stage, changed_by, note=""):
        if not changed_by.is_active or changed_by.role != User.Role.HR:
            raise ValidationError("Chỉ HR được chuyển trạng thái.")
        with transaction.atomic():
            application = Application.objects.select_for_update().get(pk=self.pk)
            allowed = self.ALLOWED_TRANSITIONS.get(application.current_stage, ())
            if to_stage not in allowed:
                raise ValidationError({"to_stage": "Chuyển trạng thái không hợp lệ."})
            from_stage = application.current_stage
            application.current_stage = to_stage
            application.save(update_fields=["current_stage", "updated_at"])
            ApplicationStatusHistory.objects.create(
                application=application, from_stage=from_stage, to_stage=to_stage,
                changed_by=changed_by, note=note,
            )
        return application

    def confirm_reward(self, confirmed_by):
        if not confirmed_by.is_active or confirmed_by.role != User.Role.HR:
            raise ValidationError("Chỉ HR được xác nhận thưởng.")
        with transaction.atomic():
            application = Application.objects.select_for_update().get(pk=self.pk)
            if application.current_stage != self.Stage.HIRED:
                raise ValidationError("Chỉ hồ sơ HIRED được xác nhận thưởng.")
            if ReferralReward.objects.filter(application=application).exists():
                raise ValidationError("Thưởng đã được xác nhận cho hồ sơ này.")
            reward = ReferralReward.objects.create(
                application=application, employee_id=application.referrer_id,
                total_amount=application.bonus_amount, confirmed_by=confirmed_by,
            )
        return reward

    def __str__(self):
        return f"Application #{self.pk} - {self.current_stage}"


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.PROTECT,
        related_name="status_history",
        verbose_name="Hồ sơ giới thiệu",
    )
    from_stage = models.CharField(
        "Trạng thái cũ", max_length=9, choices=Application.Stage.choices
    )
    to_stage = models.CharField(
        "Trạng thái mới", max_length=9, choices=Application.Stage.choices
    )
    note = models.TextField("Ghi chú nội bộ", blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="application_status_changes",
        verbose_name="Người chuyển trạng thái",
    )
    changed_at = models.DateTimeField("Thời gian chuyển trạng thái", auto_now_add=True)

    class Meta:
        verbose_name = "Lịch sử hồ sơ"
        verbose_name_plural = "Lịch sử hồ sơ"
        ordering = ["changed_at", "id"]

    def __str__(self):
        return f"Application #{self.application_id}: {self.from_stage} → {self.to_stage}"


class ReferralReward(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.PROTECT,
        related_name="reward",
        verbose_name="Hồ sơ giới thiệu",
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="referral_rewards",
        verbose_name="Người nhận thưởng",
    )
    total_amount = models.DecimalField(
        "Số tiền thưởng",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="confirmed_rewards",
        verbose_name="HR xác nhận",
    )
    created_at = models.DateTimeField("Thời gian xác nhận", auto_now_add=True)

    class Meta:
        verbose_name = "Thưởng giới thiệu"
        verbose_name_plural = "Thưởng giới thiệu"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="reward_amount_nonnegative",
            ),
        ]

    def __str__(self):
        return f"Thưởng application #{self.application_id}: {self.total_amount}"
