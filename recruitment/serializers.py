from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import (
    Application, ApplicationStatusHistory, Candidate, JobPost, ReferralReward,
)
from .utils import normalize_phone
from .validators import validate_cv


class JobPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = (
            "id",
            "title",
            "department",
            "description",
            "requirements",
            "number_of_positions",
            "bonus",
            "status",
            "deadline",
            "created_by",
            "created_at",
            "updated_at",
            "is_deleted",
        )
        read_only_fields = (
            "id", "created_by", "created_at", "updated_at", "is_deleted"
        )

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save(update_fields=[*validated_data, "updated_at"])
        instance.refresh_from_db()
        return instance


class CandidateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(max_length=20)

    class Meta:
        model = Candidate
        fields = (
            "id", "full_name", "email", "phone", "address", "dob",
            "working_experience", "note", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_phone(self, value):
        try:
            value = normalize_phone(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)
        candidates = Candidate.objects.filter(phone=value)
        if self.instance:
            candidates = candidates.exclude(pk=self.instance.pk)
        if candidates.exists():
            raise serializers.ValidationError("Số điện thoại đã thuộc hồ sơ khác.")
        return value


class EmployeeCandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = (
            "id", "full_name", "email", "phone", "address", "dob",
            "working_experience",
        )
        read_only_fields = fields


class EmployeeApplicationSerializer(serializers.ModelSerializer):
    candidate = EmployeeCandidateSerializer(read_only=True)
    cv = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = (
            "id", "job", "candidate", "referrer", "cv", "current_stage",
            "bonus_amount", "applied_at", "updated_at",
        )
        read_only_fields = fields

    def get_cv(self, application):
        if not application.cv:
            return None
        return reverse(
            "recruitment:application-cv",
            kwargs={"pk": application.pk},
            request=self.context.get("request"),
        )


class HRApplicationSerializer(EmployeeApplicationSerializer):
    candidate = CandidateSerializer(read_only=True)

    class Meta(EmployeeApplicationSerializer.Meta):
        fields = EmployeeApplicationSerializer.Meta.fields + ("note",)
        read_only_fields = EmployeeApplicationSerializer.Meta.fields

    def update(self, instance, validated_data):
        instance.note = validated_data.get("note", instance.note)
        instance.save(update_fields=["note", "updated_at"])
        instance.refresh_from_db()
        return instance


class ApplicationCreateSerializer(serializers.Serializer):
    job = serializers.PrimaryKeyRelatedField(queryset=JobPost.objects.all())
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(max_length=30)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    dob = serializers.DateField(required=False, allow_null=True, default=None)
    working_experience = serializers.CharField(required=False, allow_blank=True, default="")
    cv = serializers.FileField(required=False, validators=[validate_cv])

    def validate_phone(self, value):
        try:
            return normalize_phone(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)

    def validate_job(self, job):
        if (
            job.status != JobPost.Status.OPEN
            or job.is_deleted
            or job.deadline < timezone.localdate()
        ):
            raise serializers.ValidationError("Job phải đang mở, còn hạn và chưa bị xóa.")
        return job

    def validate(self, attrs):
        user = self.context["request"].user
        try:
            employee_phone = normalize_phone(user.phone)
        except DjangoValidationError:
            employee_phone = None
        if (
            attrs["phone"] == employee_phone
            or attrs["email"].strip().lower() == user.email.strip().lower()
        ):
            raise serializers.ValidationError("Không được giới thiệu chính mình.")
        return attrs

    def create(self, validated_data):
        job_id = validated_data.pop("job").pk
        cv = validated_data.pop("cv", None)
        phone = validated_data.pop("phone")
        referrer = self.context["request"].user
        try:
            with transaction.atomic():
                # Khóa job để hai yêu cầu cùng job không tạo hồ sơ trùng.
                job = JobPost.objects.select_for_update().get(pk=job_id)
                self.validate_job(job)
                candidate, _ = Candidate.objects.get_or_create(
                    phone=phone, defaults=validated_data
                )
                if candidate.email.strip().lower() == referrer.email.strip().lower():
                    raise serializers.ValidationError("Không được giới thiệu chính mình.")
                if Application.objects.filter(candidate=candidate, job=job).exists():
                    raise serializers.ValidationError(
                        "Ứng viên đã được giới thiệu vào job này."
                    )
                return Application.objects.create(
                    job=job,
                    candidate=candidate,
                    referrer=referrer,
                    cv=cv,
                    bonus_amount=job.bonus,
                )
        except JobPost.DoesNotExist:
            raise serializers.ValidationError({"job": "Job không còn tồn tại."})
        except IntegrityError:
            raise serializers.ValidationError("Hồ sơ đã tồn tại. Vui lòng kiểm tra lại.")


class ApplicationCVSerializer(serializers.Serializer):
    cv = serializers.FileField(validators=[validate_cv])


class ApplicationStageSerializer(serializers.Serializer):
    to_stage = serializers.ChoiceField(choices=Application.Stage.choices)
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_to_stage(self, value):
        allowed = Application.ALLOWED_TRANSITIONS.get(self.instance.current_stage, ())
        if value not in allowed:
            raise serializers.ValidationError(
                f"Không thể chuyển từ {self.instance.current_stage} sang {value}."
            )
        return value


class EmployeeStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStatusHistory
        fields = ("id", "application", "from_stage", "to_stage", "changed_at")
        read_only_fields = fields


class HRStatusHistorySerializer(EmployeeStatusHistorySerializer):
    class Meta(EmployeeStatusHistorySerializer.Meta):
        fields = EmployeeStatusHistorySerializer.Meta.fields + ("changed_by", "note")
        read_only_fields = fields


class ReferralRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralReward
        fields = (
            "id", "application", "employee", "total_amount", "confirmed_by", "created_at",
        )
        read_only_fields = fields
