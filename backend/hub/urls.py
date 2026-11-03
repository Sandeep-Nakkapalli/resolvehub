from django.urls import path

from . import api, views


urlpatterns = [
    path("", views.page, {"template_name": "index.html"}, name="home"),
    path("index.html", views.page, {"template_name": "index.html"}, name="index"),
    path("login.html", views.page, {"template_name": "login.html"}, name="login"),
    path("register.html", views.page, {"template_name": "register.html"}, name="register"),
    path("sectors.html", views.page, {"template_name": "sectors.html"}, name="sectors-page"),
    path("complaint-form.html", views.page, {"template_name": "complaint-form.html"}, name="complaint-form"),
    path("track-complaint.html", views.page, {"template_name": "track-complaint.html"}, name="track-page"),
    path("user-dashboard.html", views.page, {"template_name": "user-dashboard.html"}, name="user-dashboard"),
    path("organization-dashboard.html", views.page, {"template_name": "organization-dashboard.html"}, name="organization-dashboard"),
    path("admin-dashboard.html", views.page, {"template_name": "admin-dashboard.html"}, name="admin-dashboard"),
    path("api/public/stats/", api.public_stats, name="public-stats"),
    path("api/auth/register/", api.register, name="api-register"),
    path("api/auth/login/", api.auth_login, name="api-login"),
    path("api/auth/logout/", api.auth_logout, name="api-logout"),
    path("api/auth/password-reset/", api.password_reset, name="api-password-reset"),
    path("api/auth/me/", api.me, name="api-me"),
    path("api/sectors/", api.sectors, name="api-sectors"),
    path("api/sectors/<int:pk>/categories/", api.sector_categories, name="api-sector-categories"),
    path("api/organizations/request/", api.organizations, name="api-organization-request"),
    path("api/organizations/", api.organizations, name="api-organizations"),
    path("api/complaints/", api.complaints, name="api-complaints"),
    path("api/complaints/track/", api.track_complaint, name="api-track-complaint"),
    path("api/complaints/<int:pk>/", api.complaint_detail, name="api-complaint-detail"),
    path("api/complaints/<int:pk>/status/", api.complaint_status, name="api-complaint-status"),
    path("api/complaints/<int:pk>/responses/", api.complaint_response, name="api-complaint-response"),
    path("api/complaints/<int:pk>/feedback/", api.feedback, name="api-feedback"),
    path("api/dashboard/user/", api.user_dashboard, name="api-user-dashboard"),
    path("api/dashboard/organization/", api.organization_dashboard, name="api-organization-dashboard"),
    path("api/dashboard/admin/", api.admin_dashboard, name="api-admin-dashboard"),
    path("api/reports/sector-wise/", api.reports_sector_wise, name="api-report-sector"),
    path("api/reports/monthly/", api.reports_monthly, name="api-report-monthly"),
    path("api/notifications/", api.notifications, name="api-notifications"),
]
