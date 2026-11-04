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

## Netlify frontend and Render Django API

Netlify serves the static HTML, CSS, and JavaScript frontend. Render runs Django, its API, and the Django admin. `netlify.toml` runs `collectstatic` and `scripts/build_netlify.py`; the script converts Django's `{% static %}` tags to static URLs and writes a same-origin proxy for `/api/*` and `/django-admin/*`. This keeps the browser's existing session-cookie and CSRF flow on the Netlify domain.

### Deploy the Django API to Render

1. In Render, create a Blueprint from this GitHub repository. The root `render.yaml` defines the `resolvehub-api` Python web service.
2. Set the prompted database environment variables to the same production MySQL database currently in use, or to a compatible managed MySQL database. Do not use SQLite for a deployed service.
3. Set `ALLOWED_HOSTS` to the Render API hostname and any frontend hostnames that Render receives in the `Host` header. Set `CSRF_TRUSTED_ORIGINS` to the full HTTPS Netlify site origin, for example `https://your-site.netlify.app`; include your custom domain origin if you use one.
4. Render runs migrations before starting the service. The generated `SECRET_KEY` is stored by Render.

The service hostname is normally `https://resolvehub-api.onrender.com`. If Render assigns a different hostname, use that hostname in the Netlify build environment variable `DJANGO_API_URL`.

### Deploy the frontend to Netlify

1. Import the same GitHub repository into Netlify and use the repository root as the base directory. `netlify.toml` supplies the build command and `dist` publish directory.
2. If the Render API hostname differs from the default, set the Netlify build environment variable `DJANGO_API_URL` to the full HTTPS API origin, such as `https://resolvehub-api.onrender.com`.
3. Deploy from `main`, then test registration, login, complaint tracking, and a dashboard API call.

The production database must be reachable from Render. If its provider restricts inbound connections, allow the Render service to connect before deploying. Keep database credentials and `SECRET_KEY` in Render's environment settings; never commit them to this repository. Uploaded evidence still needs durable object storage because Render's local filesystem is not persistent across deploys.
