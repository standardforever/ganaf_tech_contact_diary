import os
import subprocess
import boto3
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Restore latest PostgreSQL backup from AWS S3'

    def handle(self, *args, **kwargs):
        s3 = boto3.client('s3')
        response = s3.list_objects_v2(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Prefix='backups/'
        )
        objects = sorted(
            response.get('Contents', []),
            key=lambda x: x['LastModified'],
            reverse=True
        )
        if not objects:
            self.stderr.write("No backups found in S3.")
            return

        latest = objects[0]['Key']
        local_path = f"/tmp/{latest.split('/')[-1]}"

        self.stdout.write(f"Downloading {latest}...")
        s3.download_file(settings.AWS_STORAGE_BUCKET_NAME, latest, local_path)

        self.stdout.write("Restoring database...")
        result = subprocess.run([
            'psql',
            '-U', settings.DATABASES['default']['USER'],
            '-h', settings.DATABASES['default']['HOST'],
            '-d', settings.DATABASES['default']['NAME'],
            '-f', local_path,
        ], env={**os.environ, 'PGPASSWORD': settings.DATABASES['default']['PASSWORD']},
            capture_output=True, text=True)

        os.remove(local_path)
        if result.returncode != 0:
            self.stderr.write(f"Restore failed: {result.stderr}")
        else:
            self.stdout.write(self.style.SUCCESS(
                "Database restored successfully."))
