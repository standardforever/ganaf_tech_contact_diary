# from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.core.management import call_command
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from unittest.mock import patch, MagicMock
from contacts.models import Contact
from io import StringIO


class ContactModelTest(TestCase):

    def setUp(self):
        self.contact = Contact.objects.create(
            name='John Doe',
            phone_number='+2348012345678',
            email='john@example.com',
            address='123 Lagos Street, Lagos',
            company='Acme Corp',
            notes='Test contact',
        )

    def test_contact_created(self):
        self.assertEqual(Contact.objects.count(), 1)

    def test_contact_str(self):
        self.assertEqual(str(self.contact), 'John Doe')

    def test_contact_fields(self):
        contact = Contact.objects.get(email='john@example.com')
        self.assertEqual(contact.name, 'John Doe')
        self.assertEqual(contact.phone_number, '+2348012345678')
        self.assertEqual(contact.address, '123 Lagos Street, Lagos')
        self.assertEqual(contact.company, 'Acme Corp')

    def test_contact_ordering(self):
        Contact.objects.create(
            name='Alice Smith',
            phone_number='+2348011111111',
            email='alice@example.com',
            address='456 Abuja Street',
        )
        contacts = Contact.objects.all()
        self.assertEqual(contacts[0].name, 'Alice Smith')
        self.assertEqual(contacts[1].name, 'John Doe')

    def test_contact_email_unique(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Contact.objects.create(
                name='Duplicate',
                phone_number='+2348099999999',
                email='john@example.com',
                address='Duplicate Address',
            )

    def test_optional_fields(self):
        contact = Contact.objects.create(
            name='No Company',
            phone_number='+2348022222222',
            email='nocompany@example.com',
            address='789 Test Street',
        )
        self.assertEqual(contact.company, '')
        self.assertEqual(contact.notes, '')


class MigrationTest(TestCase):

    def test_migration_0001_initial_applied(self):
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan([('contacts', '0001_initial')])
        self.assertEqual(len(plan), 0)

    def test_migration_0002_backup_schedule_applied(self):
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(
            [('contacts', '0002_create_backup_schedule')]
        )
        self.assertEqual(len(plan), 0)

    def test_periodic_task_registered(self):
        from django_celery_beat.models import PeriodicTask
        task = PeriodicTask.objects.filter(name='Auto DB Backup').first()
        self.assertIsNotNone(task)
        self.assertEqual(task.task, 'contacts.tasks.auto_backup')
        self.assertTrue(task.enabled)

    def test_backup_interval_schedule(self):
        from django_celery_beat.models import PeriodicTask
        from django.conf import settings
        task = PeriodicTask.objects.get(name='Auto DB Backup')
        self.assertEqual(
            task.interval.every,
            getattr(settings, 'BACKUP_INTERVAL_HOURS', 24)
        )
        self.assertEqual(task.interval.period, 'hours')


class BackupCommandTest(TestCase):

    @patch('contacts.management.commands.backup_db.boto3.client')
    @patch('contacts.management.commands.backup_db.subprocess.run')
    def test_backup_db_success(self, mock_run, mock_boto3):
        mock_run.return_value = MagicMock(returncode=0, stderr='')
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3

        out = StringIO()
        call_command('backup_db', stdout=out)

        self.assertTrue(mock_run.called)
        self.assertTrue(mock_s3.upload_file.called)
        self.assertIn('uploaded successfully', out.getvalue())

    @patch('contacts.management.commands.backup_db.subprocess.run')
    def test_backup_db_pg_dump_fails(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr='pg_dump: error'
        )

        err = StringIO()
        call_command('backup_db', stderr=err)
        self.assertIn('pg_dump failed', err.getvalue())


class RestoreCommandTest(TestCase):

    @patch('contacts.management.commands.restore_db.boto3.client')
    @patch('contacts.management.commands.restore_db.subprocess.run')
    def test_restore_db_success(self, mock_run, mock_boto3):
        mock_run.return_value = MagicMock(returncode=0, stderr='')
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'backups/backup_20260429_010101.sql',
                    'LastModified': '2026-04-29T01:01:01Z',
                }
            ]
        }

        out = StringIO()
        call_command('restore_db', stdout=out)

        self.assertTrue(mock_s3.download_file.called)
        self.assertTrue(mock_run.called)
        self.assertIn('restored successfully', out.getvalue())

    @patch('contacts.management.commands.restore_db.boto3.client')
    def test_restore_db_no_backups(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.list_objects_v2.return_value = {'Contents': []}

        err = StringIO()
        call_command('restore_db', stderr=err)
        self.assertIn('No backups found', err.getvalue())
