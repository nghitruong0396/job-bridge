from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Sum
from django.http import FileResponse
from django.utils import timezone
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import IsEmployee, IsHR

from .models import Application, Candidate, JobPost, ReferralReward
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationCVSerializer,
    ApplicationStageSerializer,
    CandidateSerializer,
    EmployeeApplicationSerializer,
    EmployeeStatusHistorySerializer,
    HRApplicationSerializer,
    HRStatusHistorySerializer,
    JobPostSerializer,
    ReferralRewardSerializer,
)


class JobPostViewSet(viewsets.ModelViewSet):
    serializer_class = JobPostSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [(IsHR | IsEmployee)()]
        return [IsHR()]

    def get_queryset(self):
        jobs = JobPost.objects.filter(is_deleted=False)
        if self.request.user.role == User.Role.HR:
            return jobs
        return jobs.filter(
            status=JobPost.Status.OPEN, deadline__gte=timezone.localdate()
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted", "updated_at"])

    @action(detail=True, methods=["post"])
    def open(self, request, pk=None):
        job = self.get_object()
        job.status = JobPost.Status.OPEN
        job.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        job = self.get_object()
        job.status = JobPost.Status.CLOSED
        job.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(job).data)


class CandidateViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    permission_classes = [IsHR]

    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError:
            raise serializers.ValidationError({"phone": "Số điện thoại đã thuộc hồ sơ khác."})


class ApplicationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    def get_permissions(self):
        if self.action in ("create", "upload_cv"):
            return [IsEmployee()]
        if self.action in ("update", "partial_update", "change_stage", "confirm_reward"):
            return [IsHR()]
        return [(IsHR | IsEmployee)()]

    def get_queryset(self):
        applications = Application.objects.select_related("candidate", "job", "referrer")
        if self.request.user.role == User.Role.HR:
            return applications
        return applications.filter(referrer=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return ApplicationCreateSerializer
        if self.action == "upload_cv":
            return ApplicationCVSerializer
        if self.action == "change_stage":
            return ApplicationStageSerializer
        if self.request.user.role == User.Role.HR:
            return HRApplicationSerializer
        return EmployeeApplicationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        response = EmployeeApplicationSerializer(
            application, context=self.get_serializer_context()
        )
        return Response(response.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def cv(self, request, pk=None):
        application = self.get_object()
        if not application.cv:
            raise NotFound("Hồ sơ chưa có CV.")
        try:
            application.cv.open("rb")
        except FileNotFoundError:
            raise NotFound("Không tìm thấy file CV.")
        return FileResponse(
            application.cv.file,
            as_attachment=True,
            filename=Path(application.cv.name).name,
        )

    @action(detail=True, methods=["post"], url_path="upload-cv")
    def upload_cv(self, request, pk=None):
        application = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application.cv = serializer.validated_data["cv"]
        application.save(update_fields=["cv", "updated_at"])
        return Response(
            EmployeeApplicationSerializer(
                application, context=self.get_serializer_context()
            ).data
        )

    @action(detail=True, methods=["post"], url_path="change-stage")
    def change_stage(self, request, pk=None):
        application = self.get_object()
        serializer = self.get_serializer(instance=application, data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            application = application.change_stage(
                changed_by=request.user, **serializer.validated_data
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                error.message_dict if hasattr(error, "message_dict") else error.messages
            )
        return Response(
            HRApplicationSerializer(
                application, context=self.get_serializer_context()
            ).data
        )

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        application = self.get_object()
        serializer_class = (
            HRStatusHistorySerializer
            if request.user.role == User.Role.HR
            else EmployeeStatusHistorySerializer
        )
        serializer = serializer_class(application.status_history.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="confirm-reward")
    def confirm_reward(self, request, pk=None):
        application = self.get_object()
        try:
            reward = application.confirm_reward(confirmed_by=request.user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)
        return Response(
            ReferralRewardSerializer(reward).data, status=status.HTTP_201_CREATED
        )


class ReferralRewardViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReferralRewardSerializer
    permission_classes = [IsHR | IsEmployee]

    def get_queryset(self):
        rewards = ReferralReward.objects.all()
        if self.request.user.role == User.Role.HR:
            return rewards
        return rewards.filter(employee=self.request.user)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        totals = self.get_queryset().aggregate(
            total_amount=Sum("total_amount"), reward_count=Count("id")
        )
        total_amount = totals["total_amount"] or Decimal("0.00")
        return Response(
            {
                "total_amount": f"{total_amount:.2f}",
                "reward_count": totals["reward_count"],
            }
        )
