from html import escape
from traceback import format_tb
from django.core import mail
from django.test import TestCase
from apps.utils.fake_traceback import FakeException, FakeTraceback
from ..mail import send_email_on_failure, send_email_on_success
from .factories import IngestTaskWatcherFactory

class MailTest(TestCase):
    def test_send_failure_email(self):
        task_watcher = IngestTaskWatcherFactory.create()
        fake_tb = FakeTraceback()
        fake_exc = FakeException('error').with_traceback(fake_tb)

        send_email_on_failure(task_watcher, fake_exc, fake_tb)

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, f'[Readux] Failed: Ingest {task_watcher.filename}')
        assert escape(format_tb(fake_tb)[0]) in mail.outbox[0].body

    def test_send_success_email(self):
        task_watcher = IngestTaskWatcherFactory.create()

        send_email_on_success(task_watcher)

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, f'[Readux] Ingest complete: {task_watcher.filename}')
