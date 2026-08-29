import random
import string
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone

from .models import Complaint, ComplaintStatusLog, Status


DEPARTMENT_CODE = "DPS"
RANDOM_SUFFIX_LENGTH = 4
MAX_ID_ATTEMPTS = 50
NON_WORKING_DAYS = {4, 5, 6}  # Friday, Saturday, Sunday
SLA_WITHIN = "Within SLA"
SLA_DUE_TODAY = "Due Today"
SLA_OVERDUE = "Overdue"


def ensure_default_statuses():
    for status_name, _label in Status.CHOICES:
        Status.objects.get_or_create(status_name=status_name)


def get_status_by_name(status_name):
    ensure_default_statuses()
    return Status.objects.get(status_name=status_name)


def generate_unique_complaint_id():
    current_year = timezone.localdate().year
    alphabet = string.ascii_uppercase + string.digits

    for _ in range(MAX_ID_ATTEMPTS):
        suffix = "".join(random.choices(alphabet, k=RANDOM_SUFFIX_LENGTH))
        complaint_id = f"{DEPARTMENT_CODE}-{current_year}-{suffix}"

        if not Complaint.objects.filter(complaint_id=complaint_id).exists():
            return complaint_id

    raise RuntimeError("Could not generate a unique complaint ID. Please try again.")


def calculate_sla(complaint_type, start_date=None):
    sla_rules = {
        Complaint.ComplaintType.PRODUCT_QUALITY: {
            "priority": Complaint.Priority.HIGH,
            "sla_days": 1,
            "is_investigative": False,
        },
        Complaint.ComplaintType.BILLING_DISPUTES: {
            "priority": Complaint.Priority.MEDIUM,
            "sla_days": 5,
            "is_investigative": False,
        },
        Complaint.ComplaintType.STAFF_CONDUCT: {
            "priority": Complaint.Priority.MEDIUM,
            "sla_days": 7,
            "is_investigative": True,
        },
    }

    if complaint_type not in sla_rules:
        raise ValueError("Invalid complaint type.")

    start_date = start_date or timezone.localdate()
    current_date = start_date
    completed_working_days = 0
    sla_days = sla_rules[complaint_type]["sla_days"]

    while completed_working_days < sla_days:
        current_date += timedelta(days=1)
        if current_date.weekday() not in NON_WORKING_DAYS:
            completed_working_days += 1

    return {
        "priority": sla_rules[complaint_type]["priority"],
        "sla_days": sla_days,
        "is_investigative": sla_rules[complaint_type]["is_investigative"],
        "target_resolution_date": current_date,
    }


def calculate_sla_status(complaint, today=None):
    today = today or timezone.localdate()

    if not complaint.target_resolution_date:
        return SLA_WITHIN

    if complaint.status.status_name in [Status.RESOLVED, Status.REJECTED]:
        final_status_date = None
        for log in complaint.status_logs.all():
            if log.new_status.status_name == complaint.status.status_name:
                final_status_date = timezone.localtime(log.changed_at).date()
                break

        if final_status_date is None and complaint.updated_at:
            final_status_date = timezone.localtime(complaint.updated_at).date()

        if final_status_date and final_status_date > complaint.target_resolution_date:
            return SLA_OVERDUE
        return SLA_WITHIN

    if today < complaint.target_resolution_date:
        return SLA_WITHIN

    if today == complaint.target_resolution_date:
        return SLA_DUE_TODAY

    return SLA_OVERDUE

def attach_sla_status(complaints):
    complaint_list = list(complaints)
    for complaint in complaint_list:
        complaint.sla_status = calculate_sla_status(complaint)
    return complaint_list

def register_complaint(citizen_name, citizen_contact, complaint_type, location, description):
    sla = calculate_sla(complaint_type)
    received_status = get_status_by_name(Status.RECEIVED)

    for _ in range(MAX_ID_ATTEMPTS):
        complaint_id = generate_unique_complaint_id()
        try:
            with transaction.atomic():
                return Complaint.objects.create(
                    complaint_id=complaint_id,
                    citizen_name=citizen_name.strip(),
                    citizen_contact=citizen_contact.strip(),
                    complaint_type=complaint_type,
                    location=location.strip(),
                    description=description.strip(),
                    status=received_status,
                    priority_assignment=sla["priority"],
                    target_resolution_date=sla["target_resolution_date"],
                    sla_days=sla["sla_days"],
                    is_investigative=sla["is_investigative"],
                )
        except IntegrityError:
            continue

    raise RuntimeError("Could not save the complaint. Please try again.")


def get_all_complaints(status=None, complaint_type=None, priority=None, search=None):
    complaints = Complaint.objects.select_related("status").prefetch_related("status_logs__new_status")

    if status:
        complaints = complaints.filter(status__status_name=status)

    if complaint_type:
        complaints = complaints.filter(complaint_type=complaint_type)

    if priority:
        complaints = complaints.filter(priority_assignment=priority)

    if search:
        clean_search = search.strip()
        complaints = complaints.filter(
            Q(complaint_id__icontains=clean_search)
            | Q(citizen_name__icontains=clean_search)
        )

    priority_order = Case(
        When(priority_assignment=Complaint.Priority.HIGH, then=Value(1)),
        When(priority_assignment=Complaint.Priority.MEDIUM, then=Value(2)),
        When(priority_assignment=Complaint.Priority.LOW, then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )

    complaints = complaints.annotate(priority_order=priority_order).order_by(
        "priority_order",
        "date_filed",
    )
    return attach_sla_status(complaints)

def search_complaint_by_id(complaint_id):
    if not complaint_id:
        return None

    complaint = (
        Complaint.objects.select_related("status")
        .prefetch_related(
            "status_logs__old_status",
            "status_logs__new_status",
            "status_logs__administrator",
        )
        .filter(complaint_id=complaint_id.strip())
        .first()
    )
    if complaint:
        complaint.sla_status = calculate_sla_status(complaint)
    return complaint


def _validate_status_transition(current_status, new_status):
    if current_status == Status.RESOLVED:
        raise ValueError("Resolved complaints can no longer be changed.")

    if current_status == new_status:
        raise ValueError("The complaint is already in that status.")

    if new_status == Status.IN_PROGRESS and current_status != Status.RECEIVED:
        raise ValueError("Invalid status transition. Complaint must be Received before it can be In Progress.")

    if new_status == Status.RESOLVED and current_status != Status.IN_PROGRESS:
        raise ValueError("Invalid status transition. Complaint must be In Progress before it can be Resolved.")

    if new_status == Status.REJECTED:
        return

    if new_status == Status.RECEIVED:
        raise ValueError("Invalid status transition. Complaint cannot be moved back to Received.")


def update_complaint_status(complaint_id, new_status, administrator, change_reason):
    """
    Stored-procedure-style status update with audit logging.

    The status update and audit log insert run in one transaction. If either
    fails, both are rolled back. The change reason is saved through Django ORM,
    so special characters are handled safely without raw SQL concatenation.
    """
    allowed_statuses = [choice[0] for choice in Status.CHOICES]
    if new_status not in allowed_statuses:
        raise ValueError("Invalid complaint status.")

    if not change_reason or not change_reason.strip():
        raise ValueError("Change reason is required.")

    with transaction.atomic():
        complaint = (
            Complaint.objects.select_for_update()
            .select_related("status")
            .filter(complaint_id=complaint_id.strip())
            .first()
        )

        if complaint is None:
            raise ValueError("Complaint ID does not exist.")

        old_status = complaint.status
        new_status_object = get_status_by_name(new_status)

        _validate_status_transition(old_status.status_name, new_status_object.status_name)

        complaint.status = new_status_object
        complaint.save(update_fields=["status", "updated_at"])

        ComplaintStatusLog.objects.create(
            complaint=complaint,
            old_status=old_status,
            new_status=new_status_object,
            administrator=administrator if getattr(administrator, "is_authenticated", False) else None,
            change_reason=change_reason.strip(),
        )

        return complaint


def get_resolved_complaints():
    """Return original complaint details for resolved complaints only."""
    complaints = (
        Complaint.objects.select_related("status")
        .prefetch_related("status_logs__new_status")
        .filter(status__status_name=Status.RESOLVED)
        .order_by("date_filed")
    )
    return attach_sla_status(complaints)


def get_dashboard_summary():
    """Return dashboard counts and recent complaints from the service layer."""
    complaints = Complaint.objects.select_related("status").prefetch_related("status_logs__new_status")
    active_complaints = attach_sla_status(
        complaints.exclude(status__status_name__in=[Status.RESOLVED, Status.REJECTED])
    )

    return {
        "total_complaints": complaints.count(),
        "total_received": complaints.filter(status__status_name=Status.RECEIVED).count(),
        "total_in_progress": complaints.filter(status__status_name=Status.IN_PROGRESS).count(),
        "total_resolved": complaints.filter(status__status_name=Status.RESOLVED).count(),
        "high_priority_count": complaints.filter(priority_assignment=Complaint.Priority.HIGH).count(),
        "within_sla_count": sum(1 for complaint in active_complaints if complaint.sla_status == SLA_WITHIN),
        "due_today_count": sum(1 for complaint in active_complaints if complaint.sla_status == SLA_DUE_TODAY),
        "overdue_count": sum(1 for complaint in active_complaints if complaint.sla_status == SLA_OVERDUE),
        "recent_complaints": attach_sla_status(complaints.order_by("-date_filed")[:5]),
    }
