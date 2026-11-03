# Generated manually for the initial ResolveHub schema.
import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import hub.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Sector",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=140, unique=True)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("description", models.TextField()),
                ("icon", models.CharField(default="layers", max_length=50)),
                ("accent", models.CharField(default="purple", max_length=30)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("account_type", models.CharField(choices=[("customer", "Customer"), ("employee", "Employee")], default="customer", max_length=20)),
                ("role", models.CharField(choices=[("customer", "Customer"), ("employee", "Employee"), ("organization_admin", "Organization administrator"), ("organization_agent", "Organization representative"), ("platform_admin", "Platform administrator")], default="customer", max_length=30)),
                ("mobile", models.CharField(max_length=20, unique=True)),
                ("state", models.CharField(max_length=100)),
                ("city", models.CharField(max_length=100)),
                ("avatar", models.ImageField(blank=True, null=True, upload_to="avatars/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"indexes": [models.Index(fields=["mobile"], name="hub_userpro_mobile_0a4c16_idx"), models.Index(fields=["role"], name="hub_userpro_role_2abbd6_idx")]},
        ),
        migrations.CreateModel(
            name="ComplaintCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("slug", models.SlugField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("sector", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="categories", to="hub.sector")),
            ],
            options={
                "ordering": ["id"],
                "constraints": [models.UniqueConstraint(fields=("sector", "name"), name="unique_category_per_sector")],
                "indexes": [models.Index(fields=["sector", "is_active"], name="hub_complai_sector__f5a7dd_idx")],
            },
        ),
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=180, unique=True)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("description", models.TextField(blank=True)),
                ("website", models.URLField(blank=True)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("is_verified", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("sector", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="organizations", to="hub.sector")),
            ],
            options={
                "ordering": ["name"],
                "indexes": [models.Index(fields=["sector", "is_active"], name="hub_organi_sector__f834d9_idx")],
            },
        ),
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("is_active", models.BooleanField(default=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="departments", to="hub.organization")),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("organization", "name"), name="unique_department_per_org")]},
        ),
        migrations.CreateModel(
            name="OrganizationUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("organization_admin", "Organization administrator"), ("organization_agent", "Organization representative")], default="organization_agent", max_length=30)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("department", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="members", to="hub.department")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="hub.organization")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="organization_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "constraints": [models.UniqueConstraint(fields=("organization", "user"), name="unique_org_user")],
                "indexes": [models.Index(fields=["user", "is_active"], name="hub_organi_user_id_9360a2_idx")],
            },
        ),
        migrations.CreateModel(
            name="Complaint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.CharField(editable=False, max_length=24, unique=True)),
                ("tracking_token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("account_type", models.CharField(choices=[("customer", "Customer"), ("employee", "Employee")], max_length=20)),
                ("title", models.CharField(max_length=220)),
                ("description", models.TextField()),
                ("incident_date", models.DateField(blank=True, null=True)),
                ("location", models.CharField(blank=True, max_length=180)),
                ("priority", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")], default="medium", max_length=20)),
                ("status", models.CharField(choices=[("submitted", "Submitted"), ("under_review", "Under Review"), ("assigned", "Assigned"), ("investigating", "Investigation in Progress"), ("action_taken", "Action Taken"), ("awaiting_user", "Awaiting User Information"), ("resolved", "Resolved"), ("rejected", "Rejected")], default="submitted", max_length=30)),
                ("due_at", models.DateTimeField(blank=True, null=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_department", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="complaints", to="hub.department")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="complaints", to="hub.complaintcategory")),
                ("complainant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="complaints", to=settings.AUTH_USER_MODEL)),
                ("current_assignee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_complaints", to=settings.AUTH_USER_MODEL)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="complaints", to="hub.organization")),
                ("sector", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="complaints", to="hub.sector")),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["complainant", "status"], name="hub_complai_complai_2dddbd_idx"),
                    models.Index(fields=["organization", "status"], name="hub_complai_organiz_5cdb46_idx"),
                    models.Index(fields=["sector", "created_at"], name="hub_complai_sector__0d6c97_idx"),
                    models.Index(fields=["public_id"], name="hub_complai_public__c1ef48_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ComplaintAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("assigned_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_assignments", to=settings.AUTH_USER_MODEL)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="received_assignments", to=settings.AUTH_USER_MODEL)),
                ("complaint", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="hub.complaint")),
                ("department", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assignments", to="hub.department")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ComplaintEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to=hub.models.complaint_upload_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=["pdf", "png", "jpg", "jpeg", "webp", "doc", "docx"])])),
                ("original_name", models.CharField(max_length=255)),
                ("file_size", models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(10485760)])),
                ("mime_type", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("complaint", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="evidence", to="hub.complaint")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploaded_evidence", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="ComplaintResponse",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField(max_length=5000)),
                ("is_internal", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="complaint_responses", to=settings.AUTH_USER_MODEL)),
                ("complaint", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="responses", to="hub.complaint")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="ComplaintStatusHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_status", models.CharField(blank=True, max_length=30)),
                ("to_status", models.CharField(choices=[("submitted", "Submitted"), ("under_review", "Under Review"), ("assigned", "Assigned"), ("investigating", "Investigation in Progress"), ("action_taken", "Action Taken"), ("awaiting_user", "Awaiting User Information"), ("resolved", "Resolved"), ("rejected", "Rejected")], max_length=30)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="status_changes", to=settings.AUTH_USER_MODEL)),
                ("complaint", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="status_history", to="hub.complaint")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(default="update", max_length=40)),
                ("title", models.CharField(max_length=180)),
                ("message", models.TextField()),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("complaint", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="hub.complaint")),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"], "indexes": [models.Index(fields=["recipient", "read_at"], name="hub_notifi_recipie_13fc84_idx")]},
        ),
        migrations.CreateModel(
            name="Feedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("comment", models.TextField(blank=True, max_length=2000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("complaint", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="feedback", to="hub.complaint")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="feedback", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=120)),
                ("entity", models.CharField(max_length=80)),
                ("entity_id", models.CharField(blank=True, max_length=80)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"], "indexes": [models.Index(fields=["entity", "entity_id"], name="hub_auditlo_entity__e8f5cc_idx"), models.Index(fields=["created_at"], name="hub_auditlo_created_3b8ea8_idx")]},
        ),
        migrations.CreateModel(
            name="OrganizationRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=180)),
                ("website", models.URLField(blank=True)),
                ("reason", models.TextField(blank=True, max_length=2000)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("declined", "Declined")], default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="organization_requests", to=settings.AUTH_USER_MODEL)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_organization_requests", to=settings.AUTH_USER_MODEL)),
                ("sector", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="organization_requests", to="hub.sector")),
            ],
        ),
    ]
