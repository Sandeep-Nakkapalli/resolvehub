from django.contrib import admin

from .models import (
    AuditLog,
    Complaint,
    ComplaintAssignment,
    ComplaintCategory,
    ComplaintEvidence,
    ComplaintResponse,
    ComplaintStatusHistory,
    Department,
    Feedback,
    Notification,
    Organization,
    OrganizationRequest,
    OrganizationUser,
    Sector,
    UserProfile,
)


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(ComplaintCategory)
class ComplaintCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sector", "is_active")
    list_filter = ("sector", "is_active")
    search_fields = ("name",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "sector", "is_verified", "is_active")
    list_filter = ("sector", "is_verified", "is_active")
    search_fields = ("name", "city")


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("public_id", "title", "organization", "status", "priority", "created_at")
    list_filter = ("status", "priority", "sector", "organization")
    search_fields = ("public_id", "title", "description")
    readonly_fields = ("public_id", "tracking_token", "created_at", "updated_at")


admin.site.register(UserProfile)
admin.site.register(OrganizationUser)
admin.site.register(Department)
admin.site.register(ComplaintAssignment)
admin.site.register(ComplaintEvidence)
admin.site.register(ComplaintResponse)
admin.site.register(ComplaintStatusHistory)
admin.site.register(Notification)
admin.site.register(Feedback)
admin.site.register(AuditLog)
admin.site.register(OrganizationRequest)
