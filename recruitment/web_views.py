from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework.exceptions import ValidationError

from accounts.decorators import role_required
from accounts.models import User

from .forms import JobPostForm, ReferralForm
from .models import JobPost
from .serializers import ApplicationCreateSerializer


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
        messages.success(request, "Đã xóa mềm tin tuyển dụng.")
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
                return redirect("recruitment_web:job-list")
        else:
            add_serializer_errors(form, serializer.errors)
    return render(request, "recruitment/referral_form.html", {"form": form, "job": job})
