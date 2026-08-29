import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


DEFAULT_STATUSES = ["Received", "In Progress", "Resolved", "Rejected"]
STATUS_MAP = {
    "Received": "Received",
    "In Progress": "In Progress",
    "Resolved": "Resolved",
    "Rejected": "Rejected",
    "Closed": "Rejected",
}
LEGACY_REASON = "Status updated before audit reason was required."


def create_statuses_and_copy_existing_values(apps, schema_editor):
    Status = apps.get_model("complaints", "Status")
    Complaint = apps.get_model("complaints", "Complaint")
    ComplaintStatusLog = apps.get_model("complaints", "ComplaintStatusLog")

    for status_name in DEFAULT_STATUSES:
        Status.objects.get_or_create(status_name=status_name)

    def status_id_for(value):
        status_name = STATUS_MAP.get(value, "Received")
        return Status.objects.get(status_name=status_name).status_id

    for complaint in Complaint.objects.all():
        complaint.status_fk_id = status_id_for(complaint.status)
        complaint.save(update_fields=["status_fk"])

    for log in ComplaintStatusLog.objects.all():
        log.old_status_fk_id = status_id_for(log.old_status)
        log.new_status_fk_id = status_id_for(log.new_status)
        log.administrator_id = log.changed_by_id
        log.change_reason = log.change_reason or LEGACY_REASON
        log.save(
            update_fields=[
                "old_status_fk",
                "new_status_fk",
                "administrator",
                "change_reason",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("complaints", "0002_complaint_is_investigative_complaint_sla_days_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Status",
            fields=[
                ("status_id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "status_name",
                    models.CharField(
                        choices=[
                            ("Received", "Received"),
                            ("In Progress", "In Progress"),
                            ("Resolved", "Resolved"),
                            ("Rejected", "Rejected"),
                        ],
                        max_length=20,
                        unique=True,
                    ),
                ),
            ],
            options={
                "ordering": ["status_id"],
                "verbose_name_plural": "Statuses",
            },
        ),
        migrations.AddField(
            model_name="complaint",
            name="status_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="complaints_temp",
                to="complaints.status",
            ),
        ),
        migrations.AddField(
            model_name="complaintstatuslog",
            name="old_status_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="old_status_logs_temp",
                to="complaints.status",
            ),
        ),
        migrations.AddField(
            model_name="complaintstatuslog",
            name="new_status_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="new_status_logs_temp",
                to="complaints.status",
            ),
        ),
        migrations.AddField(
            model_name="complaintstatuslog",
            name="administrator",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="complaintstatuslog",
            name="change_reason",
            field=models.TextField(default=LEGACY_REASON),
            preserve_default=False,
        ),
        migrations.RunPython(create_statuses_and_copy_existing_values, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="complaint",
            name="status",
        ),
        migrations.RenameField(
            model_name="complaint",
            old_name="status_fk",
            new_name="status",
        ),
        migrations.AlterField(
            model_name="complaint",
            name="status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="complaints",
                to="complaints.status",
            ),
        ),
        migrations.RemoveField(
            model_name="complaintstatuslog",
            name="old_status",
        ),
        migrations.RemoveField(
            model_name="complaintstatuslog",
            name="new_status",
        ),
        migrations.RemoveField(
            model_name="complaintstatuslog",
            name="changed_by",
        ),
        migrations.RenameField(
            model_name="complaintstatuslog",
            old_name="id",
            new_name="audit_id",
        ),
        migrations.RenameField(
            model_name="complaintstatuslog",
            old_name="old_status_fk",
            new_name="old_status",
        ),
        migrations.RenameField(
            model_name="complaintstatuslog",
            old_name="new_status_fk",
            new_name="new_status",
        ),
        migrations.AlterField(
            model_name="complaintstatuslog",
            name="audit_id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="complaintstatuslog",
            name="old_status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="old_status_logs",
                to="complaints.status",
            ),
        ),
        migrations.AlterField(
            model_name="complaintstatuslog",
            name="new_status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="new_status_logs",
                to="complaints.status",
            ),
        ),
    ]
