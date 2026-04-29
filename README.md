# Contact Diary

A Django-based contact management app with automated cloud backup,
built for local production using Docker.

## Tech Stack

- **Backend**: Django + Gunicorn
- **Database**: PostgreSQL
- **Task Queue**: Celery + Redis
- **Cloud Backup**: AWS S3
- **Reverse Proxy**: Nginx (HTTPS via mkcert)
- **Containerisation**: Docker + Docker Compose

## Getting Started

### Prerequisites

- Docker & Docker Compose
- mkcert (for SSL)

### Setup

1. Clone the repository:
   git clone https://github.com/standardforever/ganaf_tech_contact_diary.git
   cd ganaf_tech_contact_diary

2. Copy the environment file and fill in your values:
   cp env.example .env

3. Generate SSL certificates:
   mkcert -install
   mkdir -p certs
   mkcert -cert-file certs/cert.pem -key-file certs/key.pem diary.local

4. Add diary.local to /etc/hosts:
   sudo sh -c 'echo "127.0.0.1 diary.local" >> /etc/hosts'

5. Start all services:
   docker compose up --build -d

6. Create a superuser:
   docker exec -it contact_diary_web python manage.py createsuperuser

### Usage

- Admin panel: https://diary.local/admin
- Manual backup: docker exec -it contact_diary_web python manage.py backup_db
- Manual restore: docker exec -it contact_diary_web python manage.py restore_db
- Run tests: docker exec -it contact_diary_web python manage.py test contacts --verbosity=2

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
