from django.contrib import admin

from .models import Complaint, ComplaintStatusLog, Status


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ("status_id", "status_name")
    search_fields = ("status_name",)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "complaint_id",
        "citizen_name",
        "complaint_type",
        "priority_assignment",
        "status",
        "target_resolution_date",
        "date_filed",
    )
    list_filter = (
        "status",
        "priority_assignment",
        "complaint_type",
        "is_investigative",
        "date_filed",
    )
    search_fields = ("complaint_id", "citizen_name", "citizen_contact", "complaint_type")
    readonly_fields = (
        "complaint_id",
        "priority_assignment",
        "target_resolution_date",
        "sla_days",
        "is_investigative",
        "date_filed",
        "updated_at",
    )

    def has_add_permission(self, request):
        # Prevent direct admin creation so registration uses register_complaint().
        return False


@admin.register(ComplaintStatusLog)
class ComplaintStatusLogAdmin(admin.ModelAdmin):
    list_display = ("audit_id", "complaint", "old_status", "new_status", "administrator", "changed_at")
    list_filter = ("old_status", "new_status", "changed_at")
    search_fields = ("complaint__complaint_id", "complaint__citizen_name")
    readonly_fields = (
        "audit_id",
        "complaint",
        "old_status",
        "new_status",
        "administrator",
        "change_reason",
        "changed_at",
    )

    def has_add_permission(self, request):
        # Status logs should be created only by update_complaint_status().
        return False
