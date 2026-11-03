from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from .models import (
    AccountType,
    Complaint,
    ComplaintCategory,
    ComplaintResponse,
    ComplaintStatus,
    Organization,
    OrganizationRequest,
    Sector,
    UserProfile,
)


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=160)
    email = serializers.EmailField()
    mobile = serializers.CharField(max_length=20)
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)
    account_type = serializers.ChoiceField(choices=AccountType.choices)
    state = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=100)
    terms_accepted = serializers.BooleanField()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_mobile(self, value):
        value = value.strip()
        if UserProfile.objects.filter(mobile=value).exists():
            raise serializers.ValidationError("An account with this mobile number already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if not attrs["terms_accepted"]:
            raise serializers.ValidationError({"terms_accepted": "You must accept the Terms and Conditions."})
        return attrs


class SectorSerializer(serializers.ModelSerializer):
    category_count = serializers.SerializerMethodField()

    class Meta:
        model = Sector
        fields = ["id", "name", "slug", "description", "icon", "accent", "category_count"]

    def get_category_count(self, obj):
        return obj.categories.filter(is_active=True).count()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintCategory
        fields = ["id", "name", "slug", "description"]


class OrganizationSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source="sector.name", read_only=True)

    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "description", "website", "city", "sector", "sector_name", "is_verified"]


class ComplaintListSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source="sector.name", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = Complaint
        fields = [
            "id", "public_id", "title", "sector", "sector_name", "organization", "organization_name",
            "category", "category_name", "status", "status_label", "priority", "priority_label",
            "created_at", "updated_at", "resolved_at",
        ]


class ComplaintDetailSerializer(ComplaintListSerializer):
    history = serializers.SerializerMethodField()
    responses = serializers.SerializerMethodField()
    evidence = serializers.SerializerMethodField()
    assigned_department_name = serializers.CharField(source="assigned_department.name", read_only=True)

    class Meta(ComplaintListSerializer.Meta):
        fields = ComplaintListSerializer.Meta.fields + [
            "description", "incident_date", "location", "assigned_department_name", "history", "responses", "evidence",
        ]

    def get_history(self, obj):
        return [
            {
                "from_status": item.from_status,
                "to_status": item.to_status,
                "status_label": item.get_to_status_display(),
                "note": item.note,
                "created_at": item.created_at,
            }
            for item in obj.status_history.all()
        ]

    def get_responses(self, obj):
        return [
            {
                "author": item.author.get_full_name() or item.author.username,
                "body": item.body,
                "is_internal": item.is_internal,
                "created_at": item.created_at,
            }
            for item in obj.responses.select_related("author").all()
            if not item.is_internal or self.context.get("include_internal", False)
        ]

    def get_evidence(self, obj):
        return [
            {"name": item.original_name, "size": item.file_size, "created_at": item.created_at}
            for item in obj.evidence.all()
        ]


class ComplaintResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintResponse
        fields = ["body", "is_internal"]


class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ComplaintStatus.choices)
    note = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    department_id = serializers.IntegerField(required=False, allow_null=True)
    assignee_id = serializers.IntegerField(required=False, allow_null=True)


class OrganizationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationRequest
        fields = ["name", "sector", "website", "reason"]
