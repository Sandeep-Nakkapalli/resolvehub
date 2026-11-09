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

## Deploy the complete Django application to Vercel

Vercel serves the pages, static files, API, and Django admin from one Django application. The repository-root `manage.py`, `requirements.txt`, and `vercel.json` configure the Python build; `backend/config/wsgi.py` and `backend/config/asgi.py` expose the app. Vercel-hosted `.vercel.app` origins are allowed for Django host and CSRF checks.

1. Import this GitHub repository into Vercel and keep the project root at the repository root.
2. Add production environment variables in Vercel: `SECRET_KEY` (a strong random value), `DEBUG=False`, `DB_ENGINE=django.db.backends.mysql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`. Use a managed MySQL database reachable from Vercel; do not use local SQLite in production.
3. If using a custom domain, add its hostname to `ALLOWED_HOSTS` and its full HTTPS origin to `CSRF_TRUSTED_ORIGINS`.
4. Apply migrations against the configured production database with `python manage.py migrate --noinput` from a trusted environment. Do not put production migrations in the Vercel build, which can run for previews as well as production.
5. Deploy from `main`, then verify registration, login, complaint tracking, static assets, and a dashboard API call.

The Vercel build collects static assets into `staticfiles/`; Vercel serves those assets from its CDN. Store uploaded evidence in durable object storage, since deployment filesystems are not persistent. Keep database credentials and `SECRET_KEY` only in Vercel environment settings or another secret manager, never in Git.

The previous Netlify and Render configurations are retained temporarily so the existing live site is not disrupted while the Vercel deployment is being verified.
