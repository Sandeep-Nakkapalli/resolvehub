# ResolveHub

ResolveHub is a Django + Django REST Framework complaint resolution platform for customers, employees, organization representatives and platform administrators. It pairs a database-driven complaint workflow with a responsive Vaporwave-inspired interface.

## Stack

- Python 3.11+
- Django 5.1 and Django REST Framework
- MySQL 8.0 (PyMySQL adapter)
- HTML5, CSS3 and vanilla JavaScript
- Chart.js and Lucide Icons through CDN assets
- Django session authentication with CSRF protection

## Project layout

```text
frontend/                 Django-served HTML, CSS and JavaScript
backend/config/           Django project configuration
backend/hub/              Models, APIs, admin and seed command
backend/hub/migrations/   Initial relational database schema
media/                    Local development evidence storage (created at runtime)
```

## Local setup

1. Install Python 3.11 or newer and MySQL 8.0.
2. Create a database and user:

```sql
CREATE DATABASE resolvehub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and `DB_PORT`.

5. Apply migrations and load the nine sectors, 45 categories, demo organizations and development accounts:

```powershell
python manage.py migrate
python manage.py seed_demo
```

6. Start Django:

```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

### SQLite fallback for a quick local UI demo

MySQL is the intended database. If MySQL is not available, set `USE_SQLITE=True` in `.env`, run migrations and seed the same way. This fallback is for local demonstration only.

## Development accounts

These accounts are created only by `seed_demo` and must be replaced for any deployed environment:

| Role | Email | Password |
|---|---|---|
| Platform admin | `admin@resolvehub.demo` | `ResolveHubAdmin!2026` |
| Customer | `customer@resolvehub.demo` | `ResolveHubUser!2026` |
| Employee | `employee@resolvehub.demo` | `ResolveHubEmployee!2026` |
| Organization admins | `org1.admin@resolvehub.demo` through `org9.admin@resolvehub.demo` | `ResolveHubOrg!2026` |

## Main routes

- `/` — public landing page
- `/login.html`, `/register.html` — authentication
- `/sectors.html` — sector and category explorer
- `/complaint-form.html` — authenticated multi-step complaint registration
- `/track-complaint.html` — public ID + identity verification tracking
- `/user-dashboard.html` — customer/employee workspace
- `/organization-dashboard.html` — organization-scoped complaint workspace
- `/admin-dashboard.html` — platform statistics and charts
- `/django-admin/` — Django administration

## API highlights

Authentication: `/api/auth/register/`, `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/password-reset/`

Catalog: `/api/sectors/`, `/api/sectors/{id}/categories/`, `/api/organizations/`

Complaints: `/api/complaints/`, `/api/complaints/{id}/`, `/api/complaints/{id}/status/`, `/api/complaints/{id}/responses/`, `/api/complaints/track/`

Dashboards: `/api/dashboard/user/`, `/api/dashboard/organization/`, `/api/dashboard/admin/`

Reports: `/api/reports/sector-wise/`, `/api/reports/monthly/`

## Security notes

- Passwords use Django's password hashing.
- Unsafe API requests use Django CSRF protection and same-origin sessions.
- Complaint APIs enforce complainant, organization membership and platform-admin scopes.
- Public tracking requires both a complaint ID and the registering email/mobile number.
- Evidence is limited to five files per complaint, 10 MB per file and an allowlist of extensions/MIME signatures.
- Sensitive actions write to `AuditLog`.
- The local email backend is configured for console output; outbound email is intentionally not enabled in this first local/demo build.

## Production checklist

Set a strong `SECRET_KEY`, `DEBUG=False`, production `ALLOWED_HOSTS`, HTTPS, secure cookie settings, a managed object store for media, SMTP delivery, backups and a production WSGI/ASGI server. Do not use the documented demo credentials outside local development.

## Vercel Services deployment

The root `vercel.json` defines two Vercel Services in one project:

- `app` — the public Django-served frontend and fallback application routes.
- `backend` — the Django API service exposed at `/api/*`.

Public routing is ordered from specific to general: `/api/(.*)` routes to `backend`, and `/(.*)` routes to `app`. The browser already calls same-origin `/api/...` paths, so no frontend URL changes or internal service binding are required. There are currently no server-side calls from one service to the other.

Configure these Vercel environment variables before deploying:

```text
SECRET_KEY=<strong-production-secret>
DEBUG=False
ALLOWED_HOSTS=<your-vercel-domain>,<your-custom-domain>
CSRF_TRUSTED_ORIGINS=https://<your-vercel-domain>,https://<your-custom-domain>
DB_ENGINE=django.db.backends.mysql
DB_NAME=<managed-mysql-database>
DB_USER=<database-user>
DB_PASSWORD=<database-password>
DB_HOST=<database-host>
DB_PORT=3306
USE_SQLITE=False
```

Run migrations and `seed_demo` against the managed database before using the deployed dashboards. Vercel's filesystem is ephemeral, so production evidence uploads should use object storage instead of local `MEDIA_ROOT`.

For local Vercel Services development, install the Vercel CLI and run:

```powershell
vercel dev -L
```
