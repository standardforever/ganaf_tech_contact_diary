## Architectural Summary — Backup Scheduling

Celery Beat with Redis as the message broker was chosen over system-level
cron for the following reasons:

- **Django-native**: The schedule is defined in `settings.py` via
  `BACKUP_INTERVAL_HOURS` and registered as a database-backed periodic
  task, keeping all configuration inside the application.

- **No shell access required**: Cron requires SSH access to the server
  to modify schedules. Celery Beat schedules can be updated at runtime
  via the Django admin panel without touching the server.

- **Docker-friendly**: Cron does not run naturally inside Docker
  containers. Celery Beat runs as its own dedicated container
  (`celery_beat`) that starts and stops with the rest of the application.
- **Redis as broker**: Redis was chosen for its simplicity and low
  latency, making it ideal for a local production environment.
