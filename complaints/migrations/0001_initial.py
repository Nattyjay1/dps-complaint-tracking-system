# Generated manually for the beginner-friendly exam project.
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Complaint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("complaint_id", models.CharField(db_index=True, editable=False, max_length=20, unique=True)),
                ("citizen_name", models.CharField(max_length=150)),
                ("citizen_contact", models.CharField(max_length=150)),
                (
                    "complaint_type",
                    models.CharField(
                        choices=[
                            ("Product Quality", "Product Quality"),
                            ("Billing/Payment Disputes", "Billing/Payment Disputes"),
                            ("Poor Staff Conduct", "Poor Staff Conduct"),
                            ("Service Delays", "Service Delays"),
                        ],
                        max_length=50,
                    ),
                ),
                ("location", models.CharField(max_length=255)),
                ("description", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Received", "Received"),
                            ("In Progress", "In Progress"),
                            ("Resolved", "Resolved"),
                            ("Closed", "Closed"),
                        ],
                        default="Received",
                        max_length=20,
                    ),
                ),
                (
                    "priority_assignment",
                    models.CharField(
                        choices=[("Low", "Low"), ("Medium", "Medium"), ("High", "High")],
                        default="Low",
                        max_length=10,
                    ),
                ),
                ("date_filed", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-date_filed"],
            },
        ),
    ]
