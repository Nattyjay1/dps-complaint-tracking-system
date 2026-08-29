from django.conf import settings
from django.db import models


class Status(models.Model):

    RECEIVED = "Received"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"

    CHOICES = [
        (RECEIVED, RECEIVED),
        (IN_PROGRESS, IN_PROGRESS),
        (RESOLVED, RESOLVED),
        (REJECTED, REJECTED),
    ]

    status_id = models.AutoField(primary_key=True)
    status_name = models.CharField(max_length=20, unique=True, choices=CHOICES)

    class Meta:
        ordering = ["status_id"]
        verbose_name_plural = "Statuses"

    def __str__(self):
        return self.status_name


class Complaint(models.Model):

    class ComplaintType(models.TextChoices):
        PRODUCT_QUALITY = "Product Quality", "Product Quality"
        BILLING_DISPUTES = "Billing Disputes", "Billing Disputes"
        STAFF_CONDUCT = "Staff Conduct", "Staff Conduct"

    class Priority(models.TextChoices):
        LOW = "Low", "Low"
        MEDIUM = "Medium", "Medium"
        HIGH = "High", "High"

    complaint_id = models.CharField(max_length=20, unique=True, db_index=True, editable=False)
    citizen_name = models.CharField(max_length=150)
    citizen_contact = models.CharField(max_length=150)
    complaint_type = models.CharField(max_length=50, choices=ComplaintType.choices)
    location = models.CharField(max_length=255)
    description = models.TextField()
    status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name="complaints")
    priority_assignment = models.CharField(max_length=10, choices=Priority.choices, default=Priority.LOW)
    target_resolution_date = models.DateField(blank=True, null=True)
    sla_days = models.PositiveSmallIntegerField(default=0)
    is_investigative = models.BooleanField(default=False)
    date_filed = models.DateTimeField(auto_now_add=True)  # Server timestamp when saved.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_filed"]

    def __str__(self):
        return f"{self.complaint_id} - {self.citizen_name}"

class ComplaintStatusLog(models.Model):

    audit_id = models.BigAutoField(primary_key=True)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="status_logs",
    )
    old_status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        related_name="old_status_logs",
    )
    new_status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        related_name="new_status_logs",
    )
    administrator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    change_reason = models.TextField()
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.complaint.complaint_id}: {self.old_status} to {self.new_status}"
