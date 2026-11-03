# ResolveHub seed data

The canonical seed data is maintained in `backend/hub/management/commands/seed_demo.py` so it can be loaded transactionally with:

```powershell
python manage.py seed_demo
```

It creates the nine supported sectors, exactly five categories per sector, demo organizations, departments and development-only accounts.
