import mimetypes
import os
from datetime import datetime, timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    AccountType,
    AuditLog,
    Complaint,
    ComplaintAssignment,
    ComplaintCategory,
    ComplaintEvidence,
    ComplaintStatus,
    ComplaintStatusHistory,
    Department,
    Feedback,
    Notification,
    Organization,
    OrganizationRequest,
    OrganizationUser,
    PlatformRole,
    Sector,
    UserProfile,
)
from .serializers import (
    CategorySerializer,
    ComplaintDetailSerializer,
    ComplaintListSerializer,
    ComplaintResponseSerializer,
    OrganizationRequestSerializer,
    OrganizationSerializer,
    RegisterSerializer,
    SectorSerializer,
    StatusUpdateSerializer,
)


def profile_for(user):
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return None


def is_platform_admin(user):
    return user.is_superuser or getattr(profile_for(user), "role", None) == PlatformRole.PLATFORM_ADMIN


def organization_memberships(user):
    return OrganizationUser.objects.filter(user=user, is_active=True).select_related("organization", "department")


def organization_ids(user):
    return organization_memberships(user).values_list("organization_id", flat=True)


def user_payload(user):
    profile = profile_for(user)
    memberships = organization_memberships(user)
    return {
        "id": user.id,
        "name": user.get_full_name() or user.username,
        "email": user.email,
        "mobile": getattr(profile, "mobile", ""),
        "role": "platform_admin" if is_platform_admin(user) else getattr(profile, "role", "customer"),
        "account_type": getattr(profile, "account_type", "customer"),
        "organizations": [{"id": item.organization_id, "name": item.organization.name} for item in memberships],
    }


def can_view_complaint(user, complaint):
    if is_platform_admin(user) or complaint.complainant_id == user.id:
        return True
    return OrganizationUser.objects.filter(user=user, organization=complaint.organization, is_active=True).exists()


def audit(user, action, entity, entity_id="", metadata=None):
    AuditLog.objects.create(
        actor=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        metadata=metadata or {},
    )


def complaint_queryset_for(user):
    base = Complaint.objects.select_related("sector", "organization", "category", "assigned_department")
    if is_platform_admin(user):
        return base
    memberships = organization_ids(user)
    return base.filter(Q(complainant=user) | Q(organization_id__in=memberships)).distinct()


def complaint_detail_response(complaint, request_user=None):
    include_internal = bool(
        request_user
        and (
            is_platform_admin(request_user)
            or OrganizationUser.objects.filter(user=request_user, organization=complaint.organization, is_active=True).exists()
        )
    )
    return ComplaintDetailSerializer(complaint, context={"include_internal": include_internal}).data


def rate_limited(request, bucket, limit, window=300):
    ip = request.META.get("REMOTE_ADDR", "unknown")
    key = f"resolvehub:rate:{bucket}:{ip}"
    count = cache.get(key, 0)
    if count >= limit:
        return True
    cache.set(key, count + 1, window)
    return False


@api_view(["GET"])
@permission_classes([AllowAny])
def public_stats(request):
    return Response({
        "supported_sectors": Sector.objects.filter(is_active=True).count(),
        "complaint_categories": ComplaintCategory.objects.filter(is_active=True, sector__is_active=True).count(),
        "tracking": "24/7",
        "user_access": "Customers & Employees",
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    if rate_limited(request, "register", 5):
        return Response({"detail": "Too many registration attempts. Try again in a few minutes."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    with transaction.atomic():
        user = User.objects.create_user(
            username=data["email"],
            email=data["email"],
            password=data["password"],
            first_name=data["full_name"].strip(),
        )
        UserProfile.objects.create(
            user=user,
            account_type=data["account_type"],
            role=data["account_type"],
            mobile=data["mobile"],
            state=data["state"].strip(),
            city=data["city"].strip(),
        )
        audit(user, "account_created", "user", user.id, {"account_type": data["account_type"]})
    login(request, user)
    return Response({"user": user_payload(user), "message": "Welcome to ResolveHub."}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_login(request):
    if rate_limited(request, "login", 10):
        return Response({"detail": "Too many login attempts. Try again in a few minutes."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    identifier = str(request.data.get("identifier", "")).strip()
    password = request.data.get("password", "")
    if not identifier or not password:
        return Response({"detail": "Email, mobile number and password are required."}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.filter(
        Q(email__iexact=identifier) | Q(username__iexact=identifier) | Q(profile__mobile=identifier)
    ).first()
    authenticated = authenticate(request, username=user.username if user else identifier, password=password)
    if not authenticated or not authenticated.is_active:
        return Response({"detail": "The credentials do not match an active account."}, status=status.HTTP_401_UNAUTHORIZED)
    login(request, authenticated)
    remember = request.data.get("remember") in [True, "true", "1", "on", "yes"]
    if not remember:
        request.session.set_expiry(0)
    audit(authenticated, "login", "user", authenticated.id)
    return Response({"user": user_payload(authenticated), "message": "Signed in successfully."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    audit(request.user, "logout", "user", request.user.id)
    logout(request)
    return Response({"message": "Signed out successfully."})


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset(request):
    email = str(request.data.get("email", "")).strip().lower()
    if not email:
        return Response({"email": ["Enter the email address on your account."]}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"message": "If an account matches, password reset instructions will be available when email delivery is enabled."})


@api_view(["GET"])
@permission_classes([AllowAny])
def sectors(request):
    queryset = Sector.objects.filter(is_active=True).prefetch_related("categories")
    return Response(SectorSerializer(queryset, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def sector_categories(request, pk):
    sector = Sector.objects.filter(pk=pk, is_active=True).first()
    if not sector:
        return Response({"detail": "Sector not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response({
        "sector": SectorSerializer(sector).data,
        "categories": CategorySerializer(sector.categories.filter(is_active=True), many=True).data,
    })


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def organizations(request):
    if request.method == "GET":
        queryset = Organization.objects.filter(is_active=True).select_related("sector")
        sector_id = request.query_params.get("sector")
        search = request.query_params.get("search")
        if sector_id:
            queryset = queryset.filter(sector_id=sector_id)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return Response(OrganizationSerializer(queryset, many=True).data)
    if not request.user.is_authenticated:
        return Response({"detail": "Sign in to request an organization."}, status=status.HTTP_401_UNAUTHORIZED)
    serializer = OrganizationRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    item = serializer.save(requested_by=request.user)
    audit(request.user, "organization_requested", "organization_request", item.id)
    return Response({"message": "Your organization request was sent for review.", "id": item.id}, status=status.HTTP_201_CREATED)


def validate_upload(upload):
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".doc", ".docx"}
    extension = os.path.splitext(upload.name)[1].lower()
    if extension not in allowed_extensions:
        raise ValueError("Evidence must be PDF, PNG, JPG, WEBP, DOC or DOCX.")
    if upload.size > 10 * 1024 * 1024:
        raise ValueError("Each evidence file must be 10 MB or smaller.")
    allowed_types = {
        "application/pdf", "image/png", "image/jpeg", "image/webp", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    content_type = getattr(upload, "content_type", "")
    if content_type and content_type not in allowed_types:
        raise ValueError("The uploaded file type is not supported.")
    header = upload.read(16)
    upload.seek(0)
    signatures = {
        ".pdf": header.startswith(b"%PDF"),
        ".png": header.startswith(b"\x89PNG"),
        ".jpg": header.startswith(b"\xff\xd8\xff"),
        ".jpeg": header.startswith(b"\xff\xd8\xff"),
        ".webp": header.startswith(b"RIFF"),
        ".docx": header.startswith(b"PK\x03\x04"),
        ".doc": header.startswith(b"\xd0\xcf\x11\xe0"),
    }
    if extension in signatures and not signatures[extension]:
        raise ValueError("The file content does not match its extension.")


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def complaints(request):
    if request.method == "GET":
        queryset = complaint_queryset_for(request.user)
        status_filter = request.query_params.get("status")
        sector_filter = request.query_params.get("sector")
        search = request.query_params.get("search")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if sector_filter:
            queryset = queryset.filter(sector_id=sector_filter)
        if search:
            queryset = queryset.filter(
                Q(public_id__icontains=search)
                | Q(title__icontains=search)
                | Q(organization__name__icontains=search)
            )
        return Response(ComplaintListSerializer(queryset[:100], many=True).data)

    required = ["sector", "organization", "category", "title", "description", "account_type"]
    missing = [field for field in required if not str(request.data.get(field, "")).strip()]
    if missing:
        return Response({"detail": f"Missing required fields: {', '.join(missing)}."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        sector = Sector.objects.get(pk=request.data["sector"], is_active=True)
        organization = Organization.objects.get(pk=request.data["organization"], is_active=True)
        category = ComplaintCategory.objects.get(pk=request.data["category"], is_active=True)
    except (Sector.DoesNotExist, Organization.DoesNotExist, ComplaintCategory.DoesNotExist, ValueError):
        return Response({"detail": "Select a valid sector, organization and category."}, status=status.HTTP_400_BAD_REQUEST)
    if organization.sector_id != sector.id or category.sector_id != sector.id:
        return Response({"detail": "The selected organization and category must belong to the selected sector."}, status=status.HTTP_400_BAD_REQUEST)
    if request.data["account_type"] not in AccountType.values:
        return Response({"detail": "Select a valid account type."}, status=status.HTTP_400_BAD_REQUEST)
    priority = request.data.get("priority", "medium")
    priority_days = {"low": 14, "medium": 7, "high": 3, "urgent": 1}
    if priority not in priority_days:
        return Response({"priority": "Choose a valid priority."}, status=status.HTTP_400_BAD_REQUEST)

    incident_date = request.data.get("incident_date") or None
    if incident_date:
        try:
            datetime.strptime(incident_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"incident_date": "Use a valid incident date."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with transaction.atomic():
            complaint = Complaint.objects.create(
                complainant=request.user,
                account_type=request.data["account_type"],
                sector=sector,
                organization=organization,
                category=category,
                title=str(request.data["title"]).strip(),
                description=str(request.data["description"]).strip(),
                incident_date=incident_date,
                location=str(request.data.get("location", "")).strip(),
                priority=priority,
                due_at=timezone.now() + timedelta(days=priority_days[priority]),
            )
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                changed_by=request.user,
                to_status=ComplaintStatus.SUBMITTED,
                note="Complaint submitted.",
            )
            Notification.objects.create(
                recipient=request.user,
                complaint=complaint,
                kind="submission",
                title="Complaint submitted",
                message=f"Your complaint {complaint.public_id} is now in the review queue.",
            )
            for member_id in OrganizationUser.objects.filter(
                organization=organization, is_active=True
            ).values_list("user_id", flat=True):
                Notification.objects.create(
                    recipient_id=member_id,
                    complaint=complaint,
                    kind="submission",
                    title="New complaint received",
                    message=f"A new complaint has been submitted to {organization.name}.",
                )
            files = request.FILES.getlist("evidence")
            if len(files) > 5:
                raise ValueError("You can attach up to five evidence files.")
            for upload in files:
                validate_upload(upload)
                ComplaintEvidence.objects.create(
                    complaint=complaint,
                    uploaded_by=request.user,
                    file=upload,
                    original_name=upload.name[:255],
                    file_size=upload.size,
                    mime_type=getattr(upload, "content_type", "") or mimetypes.guess_type(upload.name)[0] or "application/octet-stream",
                )
            audit(request.user, "complaint_created", "complaint", complaint.id, {"public_id": complaint.public_id})
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({
        "message": "Your complaint was registered.",
        "complaint": complaint_detail_response(complaint, request.user),
        "tracking_id": complaint.public_id,
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def complaint_detail(request, pk):
    complaint = Complaint.objects.select_related("sector", "organization", "category", "assigned_department").filter(pk=pk).first()
    if not complaint or not can_view_complaint(request.user, complaint):
        return Response({"detail": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(complaint_detail_response(complaint, request.user))


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def complaint_status(request, pk):
    complaint = Complaint.objects.select_related("organization").filter(pk=pk).first()
    if not complaint:
        return Response({"detail": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)
    authorized = is_platform_admin(request.user) or OrganizationUser.objects.filter(
        user=request.user, organization=complaint.organization, is_active=True
    ).exists()
    if not authorized:
        return Response({"detail": "You are not authorized to update this complaint."}, status=status.HTTP_403_FORBIDDEN)
    serializer = StatusUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    old_status = complaint.status
    department = None
    if data.get("department_id"):
        department = Department.objects.filter(
            pk=data["department_id"], organization=complaint.organization, is_active=True
        ).first()
        if not department:
            return Response({"detail": "Select a department belonging to this organization."}, status=status.HTTP_400_BAD_REQUEST)
    assignee = None
    if data.get("assignee_id"):
        assignee = User.objects.filter(
            pk=data["assignee_id"],
            organization_memberships__organization=complaint.organization,
            organization_memberships__is_active=True,
        ).first()
        if not assignee:
            return Response({"detail": "Select an active representative from this organization."}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        complaint.status = data["status"]
        if department:
            complaint.assigned_department = department
        if assignee:
            complaint.current_assignee = assignee
        complaint.save()
        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            changed_by=request.user,
            from_status=old_status,
            to_status=complaint.status,
            note=data.get("note", ""),
        )
        if department or assignee:
            ComplaintAssignment.objects.create(
                complaint=complaint,
                assigned_by=request.user,
                assigned_to=assignee,
                department=department,
                notes=data.get("note", ""),
            )
        Notification.objects.create(
            recipient=complaint.complainant,
            complaint=complaint,
            kind="status",
            title="Complaint status updated",
            message=f"{complaint.public_id} is now {complaint.get_status_display()}.",
        )
        if assignee and assignee.id != complaint.complainant_id:
            Notification.objects.create(
                recipient=assignee,
                complaint=complaint,
                kind="assignment",
                title="Complaint assigned to you",
                message=f"{complaint.public_id} has been assigned to your queue.",
            )
        audit(request.user, "complaint_status_updated", "complaint", complaint.id, {"from": old_status, "to": complaint.status})
    return Response({"message": "Complaint updated.", "complaint": complaint_detail_response(complaint, request.user)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complaint_response(request, pk):
    complaint = Complaint.objects.select_related("organization").filter(pk=pk).first()
    if not complaint or not can_view_complaint(request.user, complaint):
        return Response({"detail": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = ComplaintResponseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    is_org_member = OrganizationUser.objects.filter(
        user=request.user, organization=complaint.organization, is_active=True
    ).exists()
    if serializer.validated_data.get("is_internal") and not (is_org_member or is_platform_admin(request.user)):
        return Response({"detail": "Only organization representatives can send internal notes."}, status=status.HTTP_403_FORBIDDEN)
    item = serializer.save(complaint=complaint, author=request.user)
    if is_org_member or is_platform_admin(request.user):
        recipient_ids = [complaint.complainant_id]
    else:
        recipient_ids = list(OrganizationUser.objects.filter(
            organization=complaint.organization, is_active=True
        ).values_list("user_id", flat=True)[:1])
    for recipient_id in recipient_ids:
        Notification.objects.create(
            recipient_id=recipient_id,
            complaint=complaint,
            kind="response",
            title="New complaint response",
            message=f"There is a new response on {complaint.public_id}.",
        )
    audit(request.user, "complaint_response_created", "complaint", complaint.id)
    return Response({"message": "Response added.", "created_at": item.created_at}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def track_complaint(request):
    if rate_limited(request, "track", 20):
        return Response({"detail": "Too many tracking attempts. Try again in a few minutes."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    public_id = str(request.data.get("complaint_id", "")).strip().upper()
    verifier = str(request.data.get("verifier", "")).strip()
    if not public_id or not verifier:
        return Response({"detail": "Complaint ID and the email or mobile number used during registration are required."}, status=status.HTTP_400_BAD_REQUEST)
    complaint = Complaint.objects.select_related("sector", "organization", "category", "assigned_department").filter(public_id=public_id).first()
    if not complaint:
        return Response({"detail": "We could not verify those tracking details."}, status=status.HTTP_404_NOT_FOUND)
    profile = profile_for(complaint.complainant)
    if complaint.complainant.email.lower() != verifier.lower() and (not profile or profile.mobile != verifier):
        return Response({"detail": "We could not verify those tracking details."}, status=status.HTTP_403_FORBIDDEN)
    data = complaint_detail_response(complaint)
    data.pop("description", None)
    data.pop("responses", None)
    data.pop("evidence", None)
    data["history"] = [{key: value for key, value in item.items() if key != "note"} for item in data.get("history", [])]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    queryset = Complaint.objects.filter(complainant=request.user)
    return Response({
        "user": user_payload(request.user),
        "counts": {
            "total": queryset.count(),
            "pending": queryset.filter(status__in=[ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, ComplaintStatus.AWAITING_USER]).count(),
            "in_progress": queryset.filter(status__in=[ComplaintStatus.ASSIGNED, ComplaintStatus.INVESTIGATING, ComplaintStatus.ACTION_TAKEN]).count(),
            "resolved": queryset.filter(status=ComplaintStatus.RESOLVED).count(),
        },
        "recent": ComplaintListSerializer(queryset.select_related("sector", "organization", "category")[:8], many=True).data,
        "notifications_unread": Notification.objects.filter(recipient=request.user, read_at__isnull=True).count(),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organization_dashboard(request):
    memberships = list(organization_memberships(request.user))
    if not memberships and not is_platform_admin(request.user):
        return Response({"detail": "No organization workspace is assigned to this account."}, status=status.HTTP_403_FORBIDDEN)
    org_filter = request.query_params.get("organization")
    membership_ids = [item.organization_id for item in memberships]
    try:
        requested_org_id = int(org_filter) if org_filter else None
    except (TypeError, ValueError):
        requested_org_id = None
    ids = [requested_org_id] if requested_org_id and (is_platform_admin(request.user) or requested_org_id in membership_ids) else membership_ids
    queryset = Complaint.objects.filter(organization_id__in=ids)
    return Response({
        "organizations": [{"id": item.organization_id, "name": item.organization.name} for item in memberships],
        "counts": {
            "received": queryset.count(),
            "pending": queryset.filter(status__in=[ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, ComplaintStatus.AWAITING_USER]).count(),
            "assigned": queryset.filter(status__in=[ComplaintStatus.ASSIGNED, ComplaintStatus.INVESTIGATING, ComplaintStatus.ACTION_TAKEN]).count(),
            "resolved": queryset.filter(status=ComplaintStatus.RESOLVED).count(),
        },
        "recent": ComplaintListSerializer(queryset.select_related("sector", "organization", "category")[:15], many=True).data,
        "departments": [{"id": item.id, "name": item.name} for item in Department.objects.filter(organization_id__in=ids, is_active=True)],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    if not is_platform_admin(request.user):
        return Response({"detail": "Administrator access is required."}, status=status.HTTP_403_FORBIDDEN)
    complaints_qs = Complaint.objects.all()
    overdue = complaints_qs.filter(due_at__lt=timezone.now()).exclude(status__in=[ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED]).count()
    sector_data = list(complaints_qs.values("sector__name").annotate(value=Count("id")).order_by("-value"))
    status_data = list(complaints_qs.values("status").annotate(value=Count("id")).order_by("status"))
    return Response({
        "counts": {
            "users": User.objects.filter(is_active=True).count(),
            "organizations": Organization.objects.filter(is_active=True).count(),
            "complaints": complaints_qs.count(),
            "pending": complaints_qs.filter(status__in=[ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, ComplaintStatus.AWAITING_USER]).count(),
            "resolved": complaints_qs.filter(status=ComplaintStatus.RESOLVED).count(),
            "overdue": overdue,
        },
        "sector_data": [{"label": item["sector__name"], "value": item["value"]} for item in sector_data],
        "status_data": status_data,
        "recent": ComplaintListSerializer(complaints_qs.select_related("sector", "organization", "category")[:12], many=True).data,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reports_sector_wise(request):
    if not is_platform_admin(request.user):
        return Response({"detail": "Administrator access is required."}, status=status.HTTP_403_FORBIDDEN)
    data = Complaint.objects.values("sector__name").annotate(total=Count("id")).order_by("sector__name")
    return Response([{"sector": item["sector__name"], "total": item["total"]} for item in data])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reports_monthly(request):
    if not is_platform_admin(request.user):
        return Response({"detail": "Administrator access is required."}, status=status.HTTP_403_FORBIDDEN)
    data = Complaint.objects.annotate(month=TruncMonth("created_at")).values("month").annotate(total=Count("id")).order_by("month")
    return Response([{"month": item["month"].strftime("%Y-%m") if item["month"] else None, "total": item["total"]} for item in data])


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def notifications(request):
    if request.method == "GET":
        items = Notification.objects.filter(recipient=request.user)[:40]
        return Response([
            {
                "id": item.id,
                "title": item.title,
                "message": item.message,
                "kind": item.kind,
                "read": bool(item.read_at),
                "created_at": item.created_at,
                "complaint_id": item.complaint.public_id if item.complaint else None,
            }
            for item in items
        ])
    item = Notification.objects.filter(pk=request.data.get("id"), recipient=request.user).first()
    if not item:
        return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
    item.read_at = timezone.now()
    item.save(update_fields=["read_at"])
    return Response({"message": "Notification marked as read."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def feedback(request, pk):
    complaint = Complaint.objects.filter(pk=pk, complainant=request.user, status=ComplaintStatus.RESOLVED).first()
    if not complaint:
        return Response({"detail": "Feedback is available for resolved complaints you submitted."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        rating = int(request.data.get("rating"))
    except (TypeError, ValueError):
        rating = 0
    if rating not in range(1, 6):
        return Response({"rating": "Choose a rating from 1 to 5."}, status=status.HTTP_400_BAD_REQUEST)
    Feedback.objects.update_or_create(
        complaint=complaint,
        defaults={
            "user": request.user,
            "rating": rating,
            "comment": str(request.data.get("comment", ""))[:2000],
        },
    )
    return Response({"message": "Thank you for sharing your feedback."}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({"user": user_payload(request.user)})
