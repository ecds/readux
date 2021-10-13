""" Model classes for ingesting volumes. """
import os
import uuid
import logging
import httpretty
from stream_unzip import stream_unzip, TruncatedDataError
from boto3 import client, resource
from io import BytesIO
from mimetypes import guess_type
from tempfile import gettempdir, mkdtemp
from zipfile import ZipFile
from tablib import Dataset
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django_celery_results.models import TaskResult
from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.tasks import add_ocr_task
from apps.iiif.canvases.services import add_ocr_annotations, get_ocr
from apps.iiif.manifests.models import Manifest, ImageServer
import apps.ingest.services as services
from apps.utils.fetch import fetch_url
from .storages import IngestStorage

LOGGER = logging.getLogger(__name__)

def bulk_path(instance, filename):
    return os.path.join('bulk', str(instance.id), filename )

class IngestTaskWatcherManager(models.Manager):
    """ Manager class for associating user and ingest data with a task result """
    def create_watcher(self, filename, task_id, task_result, task_creator):
        """
        Creates an instance of IngestTaskWatcher with provided params
        """
        watcher = self.create(
            filename=filename,
            task_id=task_id,
            task_result=task_result,
            task_creator=task_creator
        )
        return watcher


class IngestTaskWatcher(models.Model):
    """ Model class for associating user and ingest data with a task result """
    filename = models.CharField(max_length=255, null=True)
    task_id = models.CharField(max_length=255, null=True)
    task_result = models.ForeignKey(TaskResult, on_delete=models.CASCADE, null=True)
    task_creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        related_name='created_tasks'
    )
    manager = IngestTaskWatcherManager()

    class Meta:
        verbose_name_plural = 'Ingest Statuses'

class IngestAbstractModel(models.Model):
    metadata = JSONField(default=dict, blank=True)
    manifest = models.ForeignKey(Manifest, on_delete=models.DO_NOTHING, null=True)

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        abstract = True


class Bulk(models.Model):
    """ Model class for bulk ingesting volumes from local files. """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image_server = models.ForeignKey(ImageServer, on_delete=models.DO_NOTHING, null=True)
    volume_files = models.FileField(blank=False, upload_to=bulk_path)

    class Meta:
        verbose_name_plural = 'Bulk'

class Local(IngestAbstractModel):
    """ Model class for ingesting a volume from local files. """
    bulk = models.ForeignKey(Bulk, related_name='local_uploads', on_delete=models.SET_NULL, null=True)
    bundle = models.FileField(blank=False, storage=IngestStorage())
    image_server = models.ForeignKey(ImageServer, on_delete=models.DO_NOTHING, null=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_locals'
    )

    class Meta:
        verbose_name_plural = 'Local'

    @property
    def s3_client(self):
        if self.image_server.storage_service == 's3':
            return client('s3')
        return None

    def open_metadata(self):
        """
        Set metadata property from extracted metadata from file.
        """
        try:
            for zipped_file, file_size, unzipped_chunks in stream_unzip(self.__zipped_chunks()):
                file_path, file_name, file_type = self.__file_info(zipped_file)
                tmp_file = bytes()
                for chunk in unzipped_chunks:
                    if file_type and not self.__is_junk(file_name) and 'metadata' in file_name:
                        tmp_file += chunk
                if len(tmp_file) > 0 and file_type and not self.__is_junk(file_name):
                    if 'csv' in file_type or 'tab-separated' in file_type:
                        metadata = Dataset().load(tmp_file.decode('utf-8-sig'))
                    elif 'officedocument' in file_type:
                        metadata = Dataset().load(BytesIO(tmp_file))
                    if metadata is not None:
                        self.metadata = services.clean_metadata(metadata.dict[0])
                        return
        except TruncatedDataError:
            # TODO: Why does `apps.ingest.tests.test_admin.IngestAdminTest.test_local_admin_save` raise this?
            pass

    def volume_to_s3(self):
        """
        Unzip and upload image and OCR files in the bundle, without loading the entire ZIP file
        into memory or any of its uncompressed files.
        """
        for zipped_file, file_size, unzipped_chunks in stream_unzip(self.__zipped_chunks()):
            file_path, file_name, file_type = self.__file_info(zipped_file)
            tmp_file = bytes()
            for chunk in unzipped_chunks:
                if file_type and not self.__is_junk(file_name):
                    tmp_file += chunk
            if file_type and not self.__is_junk(file_name):
                file_name = file_name.replace('_', '-')
                if 'image' in file_type and 'images' in file_path:
                    self.image_server.bucket.upload_fileobj(BytesIO(tmp_file), f'{self.manifest.pid}/{file_name}')
                if 'text' in file_type and 'ocr' in file_path:
                    self.image_server.bucket.upload_fileobj(BytesIO(tmp_file), f'{self.manifest.pid}/_*ocr*_/{file_name}')

    @property
    def file_list(self):
        """Returns a list of files in the zip. Used for testing.

        :return: List of files in zip.
        :rtype: list
        """
        files = []
        for zipped_file, file_size, unzipped_chunks in stream_unzip(self.__zipped_chunks()):
            file_path, file_name, file_type = self.__file_info(zipped_file)
            files.append(file_path)
            # Not looping through the chunks throws an UnexpectedSignatureError
            for chunk in unzipped_chunks:
                pass

        return files

    def create_canvases(self):
        """
        Create Canvas objects for each image file.
        """
        self.volume_to_s3()

        image_files = [
            file.key for file in self.image_server.bucket.objects.filter(Prefix=f'{self.manifest.pid}/') if '_*ocr*_' not in file.key and file.key.split('/')[0] == self.manifest.pid
        ]

        if len(image_files) == 0:
            # TODO: Throw an error here?
            pass

        ocr_files = [
            file.key for file in self.image_server.bucket.objects.filter(Prefix=f'{self.manifest.pid}/') if '_*ocr*_' in file.key and file.key.split('/')[0] == self.manifest.pid
        ]

        for index, key in enumerate(sorted(image_files)):
            image_file = key.split('/')[-1].replace('_', '-')

            if not image_file:
                continue

            LOGGER.debug(f'Creating canvas from {image_file}')

            ocr_file_path = None
            if len(ocr_files) > 0:
                image_name = '.'.join(image_file.split('.')[:-1])

                try:
                    ocr_key = [key for key in ocr_files if image_name in key][0]
                    ocr_file_path = ocr_key
                except IndexError:
                    # Every image may not have a matching OCR file
                    ocr_file_path = None
                    pass

            position = index + 1
            canvas, created = Canvas.objects.get_or_create(
                manifest=self.manifest,
                pid=f'{self.manifest.pid}_{image_file}',
                ocr_file_path=ocr_file_path,
                position=position
            )

            if created and canvas.ocr_file_path is not None:
                if os.environ['DJANGO_ENV'] == 'test':
                    add_ocr_task(canvas.id)
                else:
                    ocr_task_id = add_ocr_task.delay(canvas.id)
                    ocr_task_result = TaskResult(task_id=ocr_task_id)
                    ocr_task_result.save()
                    IngestTaskWatcher.manager.create_watcher(
                        task_id=ocr_task_id,
                        task_result=ocr_task_result,
                        task_creator=self.creator,
                        filename=canvas.ocr_file_path
                    )


        if self.manifest.canvas_set.count() == len(image_files):
            self.delete()
        else:
            # TODO: Log or though an error/waring?
            pass

    @staticmethod
    def __is_junk(path):
        file = path.split('/')[-1]
        return file.startswith('.') or file.startswith('~') or file.startswith('__')

    @staticmethod
    def __file_info(path):
        path = path.decode('UTF-8')
        return [
            path,
            path.split('/')[-1],
            guess_type(path)[0]
        ]

    def __zipped_chunks(self):
        yield from self.bundle.file.obj.get()['Body'].iter_chunks(chunk_size=10240)

class Remote(IngestAbstractModel):
    """ Model class for ingesting a volume from remote manifest. """
    remote_url = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Remote'

    @property
    def image_server(self):
        """ Image server the Manifest """
        iiif_url = services.extract_image_server(
            self.remote_manifest['sequences'][0]['canvases'][0]
        )
        server, _created = ImageServer.objects.get_or_create(server_base=iiif_url)

        return server

    @property
    def remote_manifest(self):
        """Serialized remote IIIF Manifest data.

        :return: IIIF Manifest
        :rtype: dict
        """
        if os.environ['DJANGO_ENV'] == 'test':
            httpretty.enable()
            httpretty.register_uri(
                httpretty.GET,
                self.remote_url,
                body=open(os.path.join(settings.APPS_DIR, 'ingest/fixtures/manifest.json')).read(),
                content_type="text/json"
            )
        return fetch_url(self.remote_url)

    def open_metadata(self):
        """ Take a remote IIIF manifest and create a derivative version. """
        if self.remote_manifest['@context'] == 'http://iiif.io/api/presentation/2/context.json':
            self.metadata = services.parse_iiif_v2_manifest(self.remote_manifest)

    def create_canvases(self):
         # TODO: What if there are multiple sequences? Is that even allowed in IIIF?
        for position, canvas in enumerate(self.remote_manifest['sequences'][0]['canvases']):
            canvas_metadata = None
            # TODO: we will need some sort of check for IIIF API version, but not
            # everyone includes a context for each canvas.
            # if canvas['@context'] == 'http://iiif.io/api/presentation/2/context.json':
            canvas_metadata = services.parse_iiif_v2_canvas(canvas)

            if canvas_metadata is not None:
                canvas, _created = Canvas.objects.get_or_create(
                    pid=canvas_metadata['pid'],
                    manifest=self.manifest,
                    position=position
                )

                for (key, value) in canvas_metadata.items():
                    setattr(canvas, key, value)
                canvas.save()
