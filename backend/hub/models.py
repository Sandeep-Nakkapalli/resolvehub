import os
import uuid
from pathlib import Path

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class AccountType(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    EMPLOYEE = "employee", "Employee"


class PlatformRole(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    EMPLOYEE = "employee", "Employee"
    ORGANIZATION_ADMIN = "organization_admin", "Organization administrator"
    ORGANIZATION_AGENT = "organization_agent", "Organization representative"
    PLATFORM_ADMIN = "platform_admin", "Platform administrator"


class ComplaintStatus(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    UNDER_REVIEW = "under_review", "Under Review"
    ASSIGNED = "assigned", "Assigned"
    INVESTIGATING = "investigating", "Investigation in Progress"
    ACTION_TAKEN = "action_taken", "Action Taken"
    AWAITING_USER = "awaiting_user", "Awaiting User Information"
    RESOLVED = "resolved", "Resolved"
    REJECTED = "rejected", "Rejected"


class Priority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class OrganizationRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    DECLINED = "declined", "Declined"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    account_type = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.CUSTOMER)
    role = models.CharField(max_length=30, choices=PlatformRole.choices, default=PlatformRole.CUSTOMER)
    mobile = models.CharField(max_length=20, unique=True)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["mobile"]), models.Index(fields=["role"])]

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Sector(models.Model):
    name = models.CharField(max_length=140, unique=True)
    slug = models.SlugField(max_length=160, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default="layers")
    accent = models.CharField(max_length=30, default="purple")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class ComplaintCategory(models.Model):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]
        constraints = [models.UniqueConstraint(fields=["sector", "name"], name="unique_category_per_sector")]
        indexes = [models.Index(fields=["sector", "is_active"])]

    def __str__(self):
        return f"{self.sector.name} / {self.name}"


class Organization(models.Model):
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name="organizations")
    name = models.CharField(max_length=180, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["sector", "is_active"])]

    def __str__(self):
        return self.name


class Department(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "name"], name="unique_department_per_org")]

    def __str__(self):
        return f"{self.organization.name} / {self.name}"


class OrganizationUser(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organization_memberships")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="members")
    role = models.CharField(max_length=30, choices=[
        (PlatformRole.ORGANIZATION_ADMIN, "Organization administrator"),
        (PlatformRole.ORGANIZATION_AGENT, "Organization representative"),
    ], default=PlatformRole.ORGANIZATION_AGENT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "user"], name="unique_org_user")]
        indexes = [models.Index(fields=["user", "is_active"])]

    def __str__(self):
        return f"{self.user.username} @ {self.organization.name}"


def complaint_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"complaints/{instance.complaint_id}/{uuid.uuid4().hex}{extension}"


class Complaint(models.Model):
    public_id = models.CharField(max_length=24, unique=True, editable=False)
    tracking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    complainant = models.ForeignKey(User, on_delete=models.PROTECT, related_name="complaints")
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name="complaints")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="complaints")
    category = models.ForeignKey(ComplaintCategory, on_delete=models.PROTECT, related_name="complaints")
    title = models.CharField(max_length=220)
    description = models.TextField()
    incident_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=180, blank=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=30, choices=ComplaintStatus.choices, default=ComplaintStatus.SUBMITTED)
    assigned_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints")
    current_assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_complaints")
    due_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["complainant", "status"]),
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["sector", "created_at"]),
            models.Index(fields=["public_id"]),
        ]

    def save(self, *args, **kwargs):
        if not self.public_id:
            year = timezone.now().year
            self.public_id = f"RH-{year}-{uuid.uuid4().hex[:8].upper()}"
        if self.status == ComplaintStatus.RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)

    def clean(self):
        if self.category_id and self.sector_id and self.category.sector_id != self.sector_id:
            raise ValidationError("The selected category does not belong to the selected sector.")
        if self.organization_id and self.sector_id and self.organization.sector_id != self.sector_id:
            raise ValidationError("The selected organization does not belong to the selected sector.")

    def __str__(self):
        return f"{self.public_id} — {self.title}"


class ComplaintAssignment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="assignments")
    assigned_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_assignments")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="received_assignments")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ComplaintEvidence(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="evidence")
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="uploaded_evidence")
    file = models.FileField(
        upload_to=complaint_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "png", "jpg", "jpeg", "webp", "doc", "docx"])],
    )
    original_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(10 * 1024 * 1024)])
    mime_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def clean(self):
        if self.file_size > 10 * 1024 * 1024:
            raise ValidationError("Evidence files must be 10 MB or smaller.")


class ComplaintResponse(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="responses")
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name="complaint_responses")
    body = models.TextField(max_length=5000)
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class ComplaintStatusHistory(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="status_history")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="status_changes")
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30, choices=ComplaintStatus.choices)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    kind = models.CharField(max_length=40, default="update")
    title = models.CharField(max_length=180)
    message = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "read_at"])]


class Feedback(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name="feedback")
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="feedback")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events")
    action = models.CharField(max_length=120)
    entity = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["entity", "entity_id"]), models.Index(fields=["created_at"])]


class OrganizationRequest(models.Model):
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organization_requests")
    name = models.CharField(max_length=180)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name="organization_requests")
    website = models.URLField(blank=True)
    reason = models.TextField(blank=True, max_length=2000)
    status = models.CharField(max_length=20, choices=OrganizationRequestStatus.choices, default=OrganizationRequestStatus.PENDING)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_organization_requests")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
