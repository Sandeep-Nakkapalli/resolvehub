from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from hub.models import (
    AccountType,
    Department,
    Organization,
    OrganizationUser,
    PlatformRole,
    Sector,
    UserProfile,
)


SECTORS = [
    ("Private Companies & Industries", "Business service issues, workplace concerns and customer support accountability.", "building-2", "purple", [
        "Delayed service delivery", "Poor customer support", "Unfair service charges", "Employee grievances", "Workplace safety issues",
    ]),
    ("Educational Sector", "A clear path for students, parents and employees to raise institutional concerns.", "graduation-cap", "cyan", [
        "Excessive institutional fees", "Delayed certificates", "Poor infrastructure", "Faculty misconduct", "Discrimination and unfair treatment",
    ]),
    ("Banking & Financial Sector", "Resolve payment, transaction, lending and service concerns with confidence.", "landmark", "pink", [
        "Incorrect bank charges and hidden fees", "Failed online transactions", "Delayed loan approval", "Unauthorized transactions", "Poor customer support",
    ]),
    ("Healthcare & Hospital Sector", "Support better patient experiences and accountable healthcare services.", "heart-pulse", "green", [
        "Excessive medical bills", "Delayed medical treatment", "Poor patient care", "Lack of hospital facilities", "Medical negligence",
    ]),
    ("IT & Software Sector", "A trusted channel for employee welfare, privacy and workplace service complaints.", "cpu", "purple", [
        "Delayed employee salaries", "Excessive workload", "Workplace discrimination", "Lack of career growth", "Data privacy and security issues",
    ]),
    ("Telecom Sector", "Bring clarity to network, billing, balance and support experiences.", "smartphone", "cyan", [
        "Poor network connectivity", "Unexpected balance deductions", "Slow internet services", "Incorrect billing", "Poor customer support",
    ]),
    ("Transportation & Logistics Sector", "Make deliveries, movement and customer support more accountable.", "truck", "pink", [
        "Delayed product delivery", "Damaged goods during transportation", "Excessive delivery charges", "Lost or missing packages", "Poor customer service",
    ]),
    ("Real Estate & Construction Sector", "Create visibility around property delivery, quality and maintenance.", "home", "purple", [
        "Delayed property delivery", "Construction quality issues", "Hidden property charges", "Property documentation issues", "Poor maintenance services",
    ]),
    ("E-commerce & Retail Sector", "A transparent route through product, delivery, refund and return concerns.", "shopping-bag", "pink", [
        "Wrong products delivered", "Delayed product delivery", "Refund delays", "Fake or misleading product descriptions", "Difficult return and replacement processes",
    ]),
]


def ensure_user(email, password, name, mobile, role, account_type=AccountType.EMPLOYEE):
    user, created = User.objects.get_or_create(username=email, defaults={"email": email, "first_name": name})
    if created:
        user.set_password(password)
    user.email = email
    user.first_name = name
    user.is_active = True
    user.save()
    UserProfile.objects.update_or_create(
        user=user,
        defaults={
            "account_type": account_type,
            "role": role,
            "mobile": mobile,
            "state": "Maharashtra",
            "city": "Mumbai",
        },
    )
    return user


class Command(BaseCommand):
    help = "Seed ResolveHub sectors, categories, demo organizations and development accounts."

    @transaction.atomic
    def handle(self, *args, **options):
        sectors = []
        for name, description, icon, accent, categories in SECTORS:
            sector, _ = Sector.objects.update_or_create(
                slug=slugify(name),
                defaults={"name": name, "description": description, "icon": icon, "accent": accent, "is_active": True},
            )
            sectors.append(sector)
            for category_name in categories:
                from hub.models import ComplaintCategory
                ComplaintCategory.objects.update_or_create(
                    sector=sector,
                    name=category_name,
                    defaults={"slug": slugify(category_name), "description": f"Report and track concerns related to {category_name.lower()}.", "is_active": True},
                )

        admin = ensure_user("admin@resolvehub.demo", "ResolveHubAdmin!2026", "ResolveHub Admin", "9000000001", PlatformRole.PLATFORM_ADMIN)
        admin.is_staff = True
        admin.is_superuser = True
        admin.save(update_fields=["is_staff", "is_superuser"])
        ensure_user("customer@resolvehub.demo", "ResolveHubUser!2026", "Demo Customer", "9000000002", PlatformRole.CUSTOMER, AccountType.CUSTOMER)
        ensure_user("employee@resolvehub.demo", "ResolveHubEmployee!2026", "Demo Employee", "9000000003", PlatformRole.EMPLOYEE, AccountType.EMPLOYEE)

        for index, sector in enumerate(sectors, start=1):
            organization, _ = Organization.objects.update_or_create(
                slug=f"{sector.slug}-demo",
                defaults={
                    "name": f"{sector.name.split('&')[0].strip()} Demo Group",
                    "sector": sector,
                    "description": f"A seeded development organization for the {sector.name.lower()}.",
                    "contact_email": f"support{index}@resolvehub.demo",
                    "city": "Mumbai",
                    "is_verified": True,
                    "is_active": True,
                },
            )
            department, _ = Department.objects.get_or_create(organization=organization, name="Customer Resolution")
            email = f"org{index}.admin@resolvehub.demo"
            user = ensure_user(email, "ResolveHubOrg!2026", f"{organization.name} Admin", f"91000000{index:02d}", PlatformRole.ORGANIZATION_ADMIN)
            OrganizationUser.objects.update_or_create(
                organization=organization,
                user=user,
                defaults={"department": department, "role": PlatformRole.ORGANIZATION_ADMIN, "is_active": True},
            )

        self.stdout.write(self.style.SUCCESS("ResolveHub demo data is ready."))
        self.stdout.write("Admin: admin@resolvehub.demo / ResolveHubAdmin!2026")
        self.stdout.write("Customer: customer@resolvehub.demo / ResolveHubUser!2026")
        self.stdout.write("Organization admins: org1.admin@resolvehub.demo through org9.admin@resolvehub.demo / ResolveHubOrg!2026")
