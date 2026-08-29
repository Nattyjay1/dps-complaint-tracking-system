from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ComplaintForm, StatusUpdateForm
from .models import Complaint, Status
from .services import (
    get_all_complaints,
    get_dashboard_summary,
    get_resolved_complaints,
    register_complaint,
    search_complaint_by_id,
    update_complaint_status,
)


@login_required
def dashboard(request):
    return render(request, "complaints/dashboard.html", get_dashboard_summary())


@login_required
def complaint_create(request):
    if request.method == "POST":
        form = ComplaintForm(request.POST)
        if form.is_valid():
            try:
                complaint = register_complaint(**form.cleaned_data)
                messages.success(
                    request,
                    f"Complaint registered successfully. Generated Complaint ID: {complaint.complaint_id}",
                )
                return redirect("complaint_detail", complaint_id=complaint.complaint_id)
            except (RuntimeError, ValueError) as error:
                messages.error(request, str(error))
    else:
        form = ComplaintForm()

    return render(request, "complaints/complaint_form.html", {"form": form})


@login_required
def complaint_list(request):
    search_query = request.GET.get("search", request.GET.get("q", "")).strip()
    selected_status = request.GET.get("status", "").strip()
    selected_complaint_type = request.GET.get("complaint_type", "").strip()
    selected_priority = request.GET.get("priority", "").strip()

    complaints = get_all_complaints(
        status=selected_status,
        complaint_type=selected_complaint_type,
        priority=selected_priority,
        search=search_query,
    )

    context = {
        "complaints": complaints,
        "search_query": search_query,
        "selected_status": selected_status,
        "selected_complaint_type": selected_complaint_type,
        "selected_priority": selected_priority,
        "status_choices": Status.CHOICES,
        "complaint_type_choices": Complaint.ComplaintType.choices,
        "priority_choices": Complaint.Priority.choices,
    }
    return render(request, "complaints/complaint_list.html", context)


@login_required
def complaint_detail(request, complaint_id):
    complaint = search_complaint_by_id(complaint_id)
    if complaint is None:
        messages.error(request, "Complaint ID does not exist.")
        return redirect("complaint_list")

    if request.method == "POST":
        form = StatusUpdateForm(request.POST)
        if form.is_valid():
            try:
                complaint = update_complaint_status(
                    complaint.complaint_id,
                    form.cleaned_data["new_status"],
                    administrator=request.user,
                    change_reason=form.cleaned_data["change_reason"],
                )
                messages.success(request, "Complaint status updated successfully.")
                return redirect("complaint_detail", complaint_id=complaint.complaint_id)
            except ValueError as error:
                messages.error(request, str(error))
    else:
        form = StatusUpdateForm(initial={"new_status": complaint.status.status_name})

    return render(
        request,
        "complaints/complaint_detail.html",
        {"complaint": complaint, "form": form},
    )


@login_required
def resolved_report(request):
    complaints = get_resolved_complaints()
    return render(
        request,
        "complaints/resolved_report.html",
        {"complaints": complaints},
    )
