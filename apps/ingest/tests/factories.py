from os.path import join
from django_celery_results.models import TaskResult
from factory.django import DjangoModelFactory, FileField
from factory import Faker, SubFactory
from django.conf import settings
from apps.users.tests.factories import UserFactory
from apps.iiif.manifests.tests.factories import ImageServerFactory, ManifestFactory
from apps.ingest.models import Bulk, Local, Remote, IngestTaskWatcher

class LocalFactory(DjangoModelFactory):
    class Meta:
        model = Local

    bundle = FileField(filename='bundle.zip', filepath=join(settings.APPS_DIR, 'ingest/fixtures/bundle.zip'))
    image_server = SubFactory(ImageServerFactory)
    manifest = None

class RemoteFactory(DjangoModelFactory):
    class Meta:
        model = Remote

    manifest = None
    remote_url = Faker('url')

class BulkFactory(DjangoModelFactory):
    class Meta:
        model = Bulk

    volume_files = FileField(filename='bundle.zip', filepath=join(settings.APPS_DIR, 'ingest/fixtures/bundle.zip'))
    image_server = SubFactory(ImageServerFactory)

class TaskResultFactory(DjangoModelFactory):
    class Meta:
        model = TaskResult

    task_id = '1'
    task_name = 'fake_task'

class IngestTaskWatcherFactory(DjangoModelFactory):
    class Meta:
        model = IngestTaskWatcher

    task_id = '1'
    filename = Faker('file_path')
    task_result = SubFactory(TaskResultFactory)
    task_creator = SubFactory(UserFactory)
    associated_manifest = SubFactory(ManifestFactory)
