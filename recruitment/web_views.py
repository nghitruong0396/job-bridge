from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework.exceptions import ValidationError

from accounts.decorators import role_required
from accounts.models import User

from .forms import (
    ApplicationCVForm, ApplicationNoteForm, ApplicationStageForm,
    CandidateForm, JobPostForm, ReferralForm,
)
from .models import Application, Candidate, JobPost, ReferralReward
from .serializers import ApplicationCreateSerializer, CandidateSerializer, HRApplicationSerializer


def visible_jobs(user):
    jobs = JobPost.objects.filter(is_deleted=False)
    if user.role == User.Role.EMPLOYEE:
        jobs = jobs.filter(status=JobPost.Status.OPEN, deadline__gte=timezone.localdate())
    return jobs


def add_serializer_errors(form, errors):
    if not isinstance(errors, dict):
        errors = {"non_field_errors": errors}
    for field, error_list in errors.items():
        field = field if field in form.fields else None
        if not isinstance(error_list, (list, tuple)):
            error_list = [error_list]
        for error in error_list:
            form.add_error(field, str(error))


@role_required(User.Role.HR, User.Role.EMPLOYEE)
def job_list(request):
    return render(request, "recruitment/job_list.html", {"jobs": visible_jobs(request.user)})


@role_required(User.Role.HR, User.Role.EMPLOYEE)
def job_detail(request, pk):
    job = get_object_or_404(visible_jobs(request.user), pk=pk)
    return render(request, "recruitment/job_detail.html", {"job": job})


@role_required(User.Role.HR)
def job_form(request, pk=None):
    job = get_object_or_404(JobPost, pk=pk, is_deleted=False) if pk else None
    form = JobPostForm(request.POST if request.method == "POST" else None, instance=job)
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        if pk:
            job.save(update_fields=[*form.fields, "updated_at"])
        else:
            job.created_by = request.user
            job.save()
        messages.success(request, "Đã lưu tin tuyển dụng.")
        return redirect("recruitment_web:job-detail", pk=job.pk)
    return render(request, "recruitment/job_form.html", {"form": form, "job": job})


@role_required(User.Role.HR)
@require_POST
def job_action(request, pk, operation):
    if operation not in ("open", "close", "delete"):
        raise Http404
    job = get_object_or_404(JobPost, pk=pk, is_deleted=False)
    if operation == "delete":
        job.is_deleted = True
        job.save(update_fields=["is_deleted", "updated_at"])
        messages.success(request, "Đã xóa tin tuyển dụng.")
        return redirect("recruitment_web:job-list")
    job.status = JobPost.Status.OPEN if operation == "open" else JobPost.Status.CLOSED
    job.save(update_fields=["status", "updated_at"])
    messages.success(request, "Đã cập nhật trạng thái tin tuyển dụng.")
    return redirect("recruitment_web:job-detail", pk=job.pk)


@role_required(User.Role.EMPLOYEE)
def refer_candidate(request, pk):
    job = get_object_or_404(visible_jobs(request.user), pk=pk)
    form = ReferralForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        data = {"job": job.pk, **form.cleaned_data}
        if not data["cv"]:
            data.pop("cv")
        serializer = ApplicationCreateSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            try:
                application = serializer.save()
            except ValidationError as error:
                add_serializer_errors(form, error.detail)
            else:
                messages.success(request, f"Giới thiệu thành công. Mã hồ sơ: #{application.pk}.")
                return redirect("recruitment_web:application-detail", pk=application.pk)
        else:
            add_serializer_errors(form, serializer.errors)
    return render(request, "recruitment/referral_form.html", {"form": form, "job": job})


def visible_applications(user):
    applications = Application.objects.select_related("candidate", "job", "referrer")
    if user.role == User.Role.EMPLOYEE:
        applications = applications.filter(referrer=user)
    return applications


def application_context(request, application, **forms):
    is_hr = request.user.role == User.Role.HR
    history = application.status_history.all()
    if is_hr:
        history = history.select_related("changed_by")
    else:
        history = history.values("from_stage", "to_stage", "changed_at")
    context = {
        "application": application,
        "history": history,
        "reward": ReferralReward.objects.filter(application=application).first(),
        "can_change_stage": bool(Application.ALLOWED_TRANSITIONS.get(application.current_stage)),
    }
    if is_hr:
        context["stage_form"] = ApplicationStageForm(application)
        context["note_form"] = ApplicationNoteForm(initial={"note": application.note})
    else:
        context["cv_form"] = ApplicationCVForm()
    context.update(forms)
    return context


@role_required(User.Role.HR, User.Role.EMPLOYEE)
def application_list(request):
    applications = visible_applications(request.user)
    stage = request.GET.get("stage", "")
    if stage:
        if stage not in Application.Stage.values:
            raise Http404
        applications = applications.filter(current_stage=stage)
    pending_reward = request.GET.get("pending_reward") == "1"
    if pending_reward:
        applications = applications.filter(current_stage=Application.Stage.HIRED, reward__isnull=True)
    return render(request, "recruitment/application_list.html", {
        "applications": applications, "stages": Application.Stage.choices,
        "selected_stage": stage, "pending_reward": pending_reward,
    })


@role_required(User.Role.HR, User.Role.EMPLOYEE)
def application_detail(request, pk):
    application = get_object_or_404(visible_applications(request.user), pk=pk)
    return render(request, "recruitment/application_detail.html", application_context(request, application))


@role_required(User.Role.HR)
@require_POST
def application_stage(request, pk):
    application = get_object_or_404(Application, pk=pk)
    form = ApplicationStageForm(application, request.POST)
    if form.is_valid():
        try:
            application.change_stage(changed_by=request.user, **form.cleaned_data)
        except DjangoValidationError as error:
            add_serializer_errors(form, error.message_dict if hasattr(error, "message_dict") else error.messages)
            application.refresh_from_db()
        else:
            messages.success(request, "Đã chuyển trạng thái và ghi Lịch sử hồ sơ.")
            return redirect("recruitment_web:application-detail", pk=pk)
    return render(request, "recruitment/application_detail.html",
                  application_context(request, application, stage_form=form))


@role_required(User.Role.HR)
@require_POST
def application_note(request, pk):
    application = get_object_or_404(Application, pk=pk)
    form = ApplicationNoteForm(request.POST)
    if form.is_valid():
        serializer = HRApplicationSerializer(instance=application, data=form.cleaned_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, "Đã lưu ghi chú nội bộ.")
            return redirect("recruitment_web:application-detail", pk=pk)
        add_serializer_errors(form, serializer.errors)
    return render(request, "recruitment/application_detail.html",
                  application_context(request, application, note_form=form))


@role_required(User.Role.HR)
@require_POST
def confirm_reward(request, pk):
    application = get_object_or_404(Application, pk=pk)
    try:
        application.confirm_reward(confirmed_by=request.user)
    except DjangoValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, "Đã xác nhận thưởng giới thiệu.")
    return redirect("recruitment_web:application-detail", pk=pk)


@role_required(User.Role.EMPLOYEE)
@require_POST
def application_cv(request, pk):
    application = get_object_or_404(visible_applications(request.user), pk=pk)
    form = ApplicationCVForm(request.POST, request.FILES)
    if form.is_valid():
        application.cv = form.cleaned_data["cv"]
        application.save(update_fields=["cv", "updated_at"])
        messages.success(request, "Đã cập nhật CV.")
        return redirect("recruitment_web:application-detail", pk=pk)
    return render(request, "recruitment/application_detail.html",
                  application_context(request, application, cv_form=form))


@role_required(User.Role.HR)
def candidate_list(request):
    return render(request, "recruitment/candidate_list.html", {"candidates": Candidate.objects.all()})


@role_required(User.Role.HR)
def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    return render(request, "recruitment/candidate_detail.html", {
        "candidate": candidate,
        "applications": candidate.applications.select_related("job", "referrer"),
    })


@role_required(User.Role.HR)
def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    form = CandidateForm(request.POST if request.method == "POST" else None, instance=candidate)
    if request.method == "POST" and form.is_valid():
        serializer = CandidateSerializer(instance=candidate, data=form.cleaned_data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save()
            except IntegrityError:
                form.add_error("phone", "Số điện thoại đã thuộc hồ sơ khác.")
            else:
                messages.success(request, "Đã cập nhật hồ sơ ứng viên.")
                return redirect("recruitment_web:candidate-detail", pk=pk)
        else:
            add_serializer_errors(form, serializer.errors)
    return render(request, "recruitment/candidate_form.html", {"candidate": candidate, "form": form})


@role_required(User.Role.HR, User.Role.EMPLOYEE)
def reward_list(request):
    rewards = ReferralReward.objects.select_related("application", "application__job", "employee")
    if request.user.role == User.Role.EMPLOYEE:
        rewards = rewards.filter(employee=request.user)
    total = rewards.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    return render(request, "recruitment/reward_list.html", {"rewards": rewards, "total_amount": total})
