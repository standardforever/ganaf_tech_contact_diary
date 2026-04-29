import os
import subprocess
import boto3
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Backup PostgreSQL database to AWS S3'

    def handle(self, *args, **kwargs):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_{timestamp}.sql"
        local_path = f"/tmp/{filename}"

        self.stdout.write("Creating database dump...")
        result = subprocess.run([
            'pg_dump',
            '-U', settings.DATABASES['default']['USER'],
            '-h', settings.DATABASES['default']['HOST'],
            '-d', settings.DATABASES['default']['NAME'],
            '-f', local_path,
        ], env={**os.environ, 'PGPASSWORD': settings.DATABASES['default']['PASSWORD']},
        capture_output=True, text=True)

        if result.returncode != 0:
            self.stderr.write(f"pg_dump failed: {result.stderr}")
            return

        self.stdout.write("Uploading to S3...")
        s3 = boto3.client('s3')
        s3.upload_file(local_path, settings.AWS_STORAGE_BUCKET_NAME, f"backups/{filename}")
        os.remove(local_path)
        self.stdout.write(self.style.SUCCESS(f"Backup {filename} uploaded successfully."))