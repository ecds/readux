""" Model classes for ingesting volumes. """
import json
import logging
import os
import uuid
from io import BytesIO
from mimetypes import guess_type
from tempfile import gettempdir

import pysftp
from boto3 import client
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.db import models
from django_celery_results.models import TaskResult
from requests import get
from stream_unzip import TruncatedDataError, stream_unzip
from tablib import Dataset

from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.tasks import add_oa_ocr_task, add_ocr_task
from apps.iiif.kollections.models import Collection
from apps.iiif.manifests.models import ImageServer, Manifest
from apps.ingest import services
from apps.utils.fetch import fetch_url

from .storages import IngestStorage

LOGGER = logging.getLogger(__name__)
logging.getLogger('botocore').setLevel(logging.ERROR)
logging.getLogger('boto3').setLevel(logging.ERROR)
logging.getLogger('s3transfer').setLevel(logging.ERROR)
logging.getLogger('httpretty').setLevel(logging.CRITICAL)
logging.getLogger('httpretty.core').setLevel(logging.CRITICAL)
logging.getLogger('paramiko').setLevel(logging.ERROR)
logging.getLogger('elasticsearch.base').setLevel(logging.ERROR)

def bulk_path(instance, filename):
    return os.path.join('bulk', str(instance.id), filename )

class IngestTaskWatcherManager(models.Manager):
    """ Manager class for associating user and ingest data with a task result """
    def create_watcher(self, filename, task_id, task_result, task_creator, associated_manifest=None):
        """
        Creates an instance of IngestTaskWatcher with provided params
        """
        watcher = self.create(
            filename=filename,
            task_id=task_id,
            task_result=task_result,
            task_creator=task_creator,
            associated_manifest=associated_manifest
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
    associated_manifest = models.ForeignKey(Manifest, on_delete=models.SET_NULL, null=True)
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
    collections = models.ManyToManyField(
        Collection,
        blank=True,
        help_text="Optional: Collections to attach to ALL volumes ingested in this form."
    )

    class Meta:
        verbose_name_plural = 'Bulk'

class Local(IngestAbstractModel):
    """ Model class for ingesting a volume from local files. """
    bulk = models.ForeignKey(Bulk, related_name='local_uploads', on_delete=models.SET_NULL, null=True)
    bundle_from_bulk = models.FileField(null=True, blank=True, upload_to=bulk_path)
    bundle = models.FileField(null=True, blank=True, storage=IngestStorage())
    image_server = models.ForeignKey(ImageServer, on_delete=models.DO_NOTHING, null=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_locals'
    )
    collections = models.ManyToManyField(
        Collection,
        blank=True,
        help_text="Optional: Collections to attach to the volume ingested in this form."
    )

    remote_dir = None
    remote_files = []

    class Meta:
        verbose_name_plural = 'Local'

    @property
    def s3_client(self):
        if self.image_server.storage_service == 's3':
            return client('s3')

        return None

    def create_sftp_connection(self):

        if self.image_server.storage_service == 'sftp':
            connection_options = pysftp.CnOpts()

            # if os.environ['DJANGO_ENV'] == 'test':
            connection_options.hostkeys = None

            return pysftp.Connection(**self.image_server.sftp_connection, cnopts=connection_options)

        return None

    def open_metadata(self):
        """
        Set metadata property from extracted metadata from file.
        """
        try:
            for zipped_file, _, unzipped_chunks in stream_unzip(self.__zipped_chunks()):
                _, file_name, file_type = self.__file_info(zipped_file)
                tmp_file = bytes()
                for chunk in unzipped_chunks:
                    if file_type and not self._is_junk(file_name) and 'metadata' in file_name:
                        tmp_file += chunk
                if len(tmp_file) > 0 and file_type and not self._is_junk(file_name):
                    if 'csv' in file_type or 'tab-separated' in file_type:
                        format = 'csv' if 'csv' in file_type else 'tsv'
                        metadata = Dataset().load(tmp_file.decode('utf-8-sig'), format=format)
                    elif 'officedocument' in file_type:
                        metadata = Dataset().load(BytesIO(tmp_file))
                    if metadata is not None:
                        self.metadata = services.clean_metadata(metadata.dict[0])
                        return
        except TruncatedDataError:
            # TODO: Why does `apps.ingest.tests.test_admin.IngestAdminTest.test_local_admin_save` raise this?
            pass

    def volume_to_s3(self):
        """ Upload images and OCR files to an S3 bucket

        :return: Tuple of two lists. One list of image files and one of OCR files
        :rtype: tuple
        """
        self.__unzip_bundle()

        return (
            [file.key for file in self.image_server.bucket.objects.filter(Prefix=f'{self.manifest.pid}/') if '_*ocr*_' not in file.key and file.key.split('/')[0] == self.manifest.pid],
            [file.key for file in self.image_server.bucket.objects.filter(Prefix=f'{self.manifest.pid}/') if '_*ocr*_' in file.key and file.key.split('/')[0] == self.manifest.pid]
        )

    def volume_to_sftp(self):
        """ Upload images and OCR files via SFTP

        :return: Tuple of two lists. One list of image files and one of OCR files
        :rtype: tuple
        """

        # sftp = self.create_sftp_connection()
        # sftp.mkdir(self.manifest.pid)
        # with sftp.cd(self.manifest.pid):
        #     sftp.mkdir('_*ocr*_')

        # sftp.close()
        self.__unzip_bundle()
        return self.__list_sftp_files()

    def bundle_to_s3(self):
        """Uploads the zipfile stored in bundle_from_bulk to S3
        :param file_path: File path for uploaded file
        :type file_path: str
        """
        if bool(self.bundle_from_bulk):
            # Save to bundle
            if not bool(self.bundle):
                if not os.path.isfile(self.bundle_from_bulk.path):
                    raise Exception(f"Could not find file: {self.bundle_from_bulk.path}")
                bulk_name = self.bundle_from_bulk.name
                with ContentFile(self.bundle_from_bulk.read()) as file_content:
                    self.bundle.save(bulk_name, file_content)

            # Delete tempfile
            key_count = client('s3').list_objects_v2(
                Bucket=self.bundle.field.storage.bucket_name,
                Prefix=f'bulk/{self.id}'
            )['KeyCount']

            assert key_count == 1

            if bool(self.bundle):
                old_path = self.bundle_from_bulk.path
                os.remove(old_path)
                dir_path = old_path[0:old_path.rindex('/')]
                if not os.path.isfile(old_path) and len(os.listdir(dir_path)) == 0:
                    os.rmdir(dir_path)
                self.bundle_from_bulk.delete()

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
            for _ in unzipped_chunks:
                pass

        return files

    def create_canvases(self):
        """
        Create Canvas objects for each image file.
        """
        image_files, ocr_files = ([], [])

        if self.image_server.storage_service == 's3':
            image_files, ocr_files = self.volume_to_s3()
        elif self.image_server.storage_service == 'sftp':
            image_files, ocr_files = self.volume_to_sftp()

        if len(image_files) == 0:
            # TODO: Throw an error here?
            pass

        for index, key in enumerate(sorted(image_files)):
            image_file = key.split('/')[-1]#.replace('_', '-')

            if not image_file:
                continue

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

            pid = image_file if self.manifest.pid in image_file else f'{self.manifest.pid}_{image_file}'
            position = index + 1
            canvas, created = Canvas.objects.get_or_create(
                manifest=self.manifest,
                pid=pid,
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

            # Request the thumbnail so a cached version is created on IIIF server.
            if os.environ['DJANGO_ENV'] != 'test':
                get(canvas.thumbnail)


        if self.manifest.canvas_set.count() == len(image_files):
            self.delete()
        else:
            # TODO: Log or though an error/waring?
            pass

    def __unzip_bundle(self):
        """
        Unzip and upload image and OCR files in the bundle, without loading the entire ZIP file
        into memory or any of its uncompressed files.
        """
        for zipped_file, _, unzipped_chunks in stream_unzip(self.__zipped_chunks()):
            file_path, file_name, file_type = self.__file_info(zipped_file)

            has_type_or_is_hocr = file_name.endswith('.hocr') or file_type
            tmp_file = bytes()
            for chunk in unzipped_chunks:
                if has_type_or_is_hocr and not self._is_junk(file_name):
                    tmp_file += chunk
            if (file_type or file_name.endswith('.hocr')) and not self._is_junk(file_name):
                file_name = file_name.replace('_', '-')
                if file_type and 'image' in file_type and 'images' in file_path:
                    self.__upload_file(tmp_file, file_name, file_path)
                if file_type:
                    is_ocr_file_type = (
                        'text' in file_type
                        or 'xml' in file_type
                        or 'json' in file_type
                        or 'html' in file_type
                    )
                if 'ocr' in file_path and (
                    file_name.endswith('.hocr') or is_ocr_file_type
                ):
                    self.__upload_file(tmp_file, file_name, file_path)

    def __upload_file(self, file, file_name, path):
        remote_path = f'{self.manifest.pid}{self.image_server.path_delineator}{file_name}'
        if self.image_server.storage_service == 's3':
            if 'ocr' in path:
                remote_path = f'{self.manifest.pid}/_*ocr*_/{file_name}'
            self.image_server.bucket.upload_fileobj(
                BytesIO(file),
                remote_path
            )
        elif self.image_server.storage_service == 'sftp':
            # Check if the file will be stored in a sub directory.
            self.remote_dir = os.path.dirname(remote_path)
            # Make any needed local directories.
            if self.remote_dir and not os.path.exists(os.path.join(gettempdir(), self.remote_dir)):
                os.makedirs(os.path.join(gettempdir(), self.remote_dir))

            # Define the full local path
            local_path = os.path.join(gettempdir(), remote_path)


            # Write the file to the local disk.
            with open(local_path, 'wb') as f:
                f.write(BytesIO(file).getbuffer())
            for _ in range(0,5):
                print(f'local {local_path}')

            sftp = self.create_sftp_connection()

            if self.remote_dir:
                # Make remote directories if needed.
                if not sftp.isdir(self.remote_dir):
                    sftp.makedirs(self.remote_dir)

                # Change to the remote directory before upload.
                sftp.chdir(self.remote_dir)

            sftp.put(local_path)
            os.remove(local_path)
            sftp.close()

        return remote_path

    def __list_sftp_files(self):
        sftp = self.create_sftp_connection()

        remote_files = []

        if self.remote_dir:
            remote_files = [remote_file for remote_file in sftp.listdir(self.manifest.pid)]
        else:
            remote_files = [remote_file for remote_file in sftp.listdir() if f'{self.manifest.pid}{self.image_server.path_delineator}' in remote_file]

        files = (
            [os.path.join(self.remote_dir, image) for image in remote_files if 'image' in guess_type(image)[0]],
            [os.path.join(self.remote_dir, ocr_file) for ocr_file in remote_files if 'image' not in guess_type(ocr_file)[0]],
        )
        sftp.close()

        return files

    @staticmethod
    def _is_junk(path):
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
        try:
            yield from self.bundle.file.obj.get()['Body'].iter_chunks(chunk_size=10240)
        except Exception as error:
            LOGGER.error(error)


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
            return json.loads(open(os.path.join(settings.APPS_DIR, 'ingest/fixtures/manifest.json')).read())

        return fetch_url(self.remote_url)

    def open_metadata(self):
        """ Take a remote IIIF manifest and create a derivative version. """
        if self.remote_manifest['@context'] == 'http://iiif.io/api/presentation/2/context.json':
            self.metadata = services.parse_iiif_v2_manifest(self.remote_manifest)

    def create_canvases(self):
        # TODO: What if there are multiple sequences? Is that even allowed in IIIF?
        for position, sc_canvas in enumerate(self.remote_manifest['sequences'][0]['canvases']):
            canvas_metadata = None
            # TODO: we will need some sort of check for IIIF API version, but not
            # everyone includes a context for each canvas.
            # if canvas['@context'] == 'http://iiif.io/api/presentation/2/context.json':
            canvas_metadata = services.parse_iiif_v2_canvas(sc_canvas)

            if canvas_metadata is not None:
                canvas, _ = Canvas.objects.get_or_create(
                    pid=canvas_metadata['pid'],
                    manifest=self.manifest,
                    position=position
                )

                for (key, value) in canvas_metadata.items():
                    setattr(canvas, key, value)
                canvas.save()
                canvas.refresh_from_db()

                if os.environ['DJANGO_ENV'] != 'test':
                    add_ocr_task.delay(canvas.id)

                if 'otherContent' in sc_canvas and len(sc_canvas['otherContent']) > 0:
                    for content in sc_canvas['otherContent']:
                        if content['label'] == 'OCR Text':
                            if os.environ['DJANGO_ENV'] != 'test':
                                add_oa_ocr_task.delay(content['@id'])
                            else:
                                add_oa_ocr_task(content['@id'])

def validate_is_csv():
    # invalid but required for old migration
    raise NotImplementedError

class S3Ingest(models.Model):
    """ Model class for bulk ingesting volumes from an Amazon AWS S3 bucket. """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    s3_bucket = models.CharField(
        null=False,
        blank=False,
        max_length=255,
        help_text="""The name of a publicly-accessible S3 bucket containing volumes to ingest,
        either at the bucket root or within subfolder(s). Each volume should have its own
        subfolder, with the volume's PID as its name.""",
    )
    s3_prefix = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text="Optional: Subfolder(s) within the S3 bucket containing your volumes to ingest.",
    )
    metadata_spreadsheet = models.FileField(
        null=False,
        blank=False,
        help_text="""A spreadsheet file (CSV) with a row for each volume, including the
        volume PID, which must match the subfolder name in the S3 bucket.""",
        validators=[FileExtensionValidator(allowed_extensions=['csv'])],
    )
    image_server = models.ForeignKey(ImageServer, on_delete=models.DO_NOTHING, null=True)
    collections = models.ManyToManyField(
        Collection,
        blank=True,
        help_text="Optional: Collections to attach to ALL volumes ingested in this form."
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_s3ingests"
    )

    class Meta:
        verbose_name_plural = 'Amazon S3 Ingests'

    def create_canvases_for(self, pid):
        """Create Canvas objects for each image file in a single volume, by pid."""
        image_files, ocr_files = ([], [])

        # get the list of all subfolders (aws parlance "Common Prefixes") at the root, specified
        # by the s3_bucket and the s3_prefix
        root_prefix = f"{self.s3_prefix}/" or ""
        s3 = client("s3")
        # use paginator in case list is > 1000 items
        paginator = s3.get_paginator("list_objects_v2")
        root = paginator.paginate(Bucket=self.s3_bucket, Prefix=root_prefix, Delimiter="/")
        for prefix_result in root.search("CommonPrefixes"):
            subfolder_name = prefix_result.get("Prefix")
            subfolder_name = subfolder_name[:-1] if subfolder_name.endswith("/") else subfolder_name
            # if this subfolder does not match the pid name, skip it
            if subfolder_name.split("/")[-1] != pid:
                continue
            LOGGER.debug(f"Subfolder found for pid: {pid}")
            subfolder_pages = paginator.paginate(
                Bucket=self.s3_bucket,
                Prefix=f"{root_prefix}{pid}/" if root_prefix else f"{pid}/",
            )
            for page in subfolder_pages:
                for s3_object in page.get("Contents"):
                    key = s3_object.get("Key")
                    # at this point, we just want to handle all files and ignore folder structure,
                    # so we can ignore keys ending in /
                    if key.endswith("/"):
                        continue
                    # determine if this is image or ocr and upload it
                    self.disambiguate_and_upload(pid, key)

            # collect all uploaded files
            image_files, ocr_files = self.image_server_paths(pid)

        # the following is adapted closely from Local.create_canvases:

        if len(image_files) == 0:
            raise Exception(f"No images found for pid {pid} in s3 bucket {self.s3_bucket}")

        # retrieve the manifest; will have been created in task function if not already present
        manifest = Manifest.objects.get(pid=pid)

        # create canvases for each image
        for index, img_key in enumerate(sorted(image_files)):
            image_file = img_key.split("/")[-1]
            if not image_file:
                continue
            ocr_file_path = None
            if len(ocr_files) > 0:
                image_name = ".".join(image_file.split(".")[:-1])
                try:
                    ocr_key = [k for k in ocr_files if image_name in k][0]
                    ocr_file_path = ocr_key
                except IndexError:
                    # Every image may not have a matching OCR file
                    ocr_file_path = None
                    pass
            canvas_pid = image_file if manifest.pid in image_file else f"{manifest.pid}_{image_file}"
            position = index + 1
            canvas, created = Canvas.objects.get_or_create(
                manifest=manifest,
                pid=canvas_pid,
                ocr_file_path=ocr_file_path,
                position=position
            )

            if created and canvas.ocr_file_path is not None:
                if os.environ["DJANGO_ENV"] == "test":
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

            # Request the thumbnail so a cached version is created on IIIF server.
            if os.environ["DJANGO_ENV"] != "test":
                get(canvas.thumbnail)

        # cleanup by deleting ingest if there is a canvas for each image
        if manifest.canvas_set.count() == len(image_files):
            self.delete()
        else:
            # TODO: Log or though an error/waring?
            pass


    def image_server_paths(self, pid):
        """ Retrieve paths from image server (S3 bucket or SFTP)

        :return: Tuple of two lists. One list of image files and one of OCR files
        :rtype: tuple
        """
        if self.image_server.storage_service == "s3":
            return (
                [
                    file.key
                    for file in self.image_server.bucket.objects.filter(
                        Prefix=f"{pid}/"
                    )
                    if "_*ocr*_" not in file.key
                    and file.key.split("/")[0] == pid
                ],
                [
                    file.key
                    for file in self.image_server.bucket.objects.filter(
                        Prefix=f"{pid}/"
                    )
                    if "_*ocr*_" in file.key
                    and file.key.split("/")[0] == pid
                ],
            )
        elif self.image_server.storage_service == "sftp":
            return self.__list_sftp_files(pid)
        return ([], [])

    def disambiguate_and_upload(self, pid, key):
        """Determine if a file is an image or OCR and send to the upload function appropriately"""
        file_path, file_name, file_type = self.__file_info(key)
        if (file_type or file_name.endswith(".hocr")) and not Local._is_junk(file_name):
            file_name = file_name.replace("_", "-")
            if file_type and "image" in file_type and "images" in file_path:
                self.__upload_file(pid, key, file_name, is_ocr=False)
            if file_type:
                is_ocr_file_type = (
                    "text" in file_type
                    or "xml" in file_type
                    or "json" in file_type
                    or "html" in file_type
                )
            if "ocr" in file_path and (
                file_name.endswith(".hocr") or is_ocr_file_type
            ):
                self.__upload_file(pid, key, file_name, is_ocr=True)

    def __upload_file(self, pid, key, file_name, is_ocr):
        """Get a file from the s3 bucket and upload to the image server"""
        # if we're uploading to s3 image server, just use s3 bucket copy function!
        remote_path = f"{pid}{self.image_server.path_delineator}{file_name}"
        if self.image_server.storage_service == "s3":
            if is_ocr:
                remote_path = f"{pid}/_*ocr*_/{file_name}"
            LOGGER.debug(f"Copying {key} to s3 bucket")
            self.image_server.bucket.copy({ "Bucket": self.s3_bucket, "Key": key }, remote_path)
        # otherwise we need to actually download the file and reupload it to sftp
        elif self.image_server.storage_service == "sftp":
            # Check if the file will be stored in a sub directory
            remote_dir = os.path.dirname(remote_path)
            # Make any needed local directories
            if remote_dir and not os.path.exists(os.path.join(gettempdir(), remote_dir)):
                os.makedirs(os.path.join(gettempdir(), remote_dir))
            # Define the full local path
            local_path = os.path.join(gettempdir(), remote_path)
            # Download the file from S3 and write the file to the local disk
            LOGGER.debug(f"Downloading {key} from s3 bucket")
            with open(local_path, "wb") as f:
                client("s3").download_fileobj(self.s3_bucket, key, f)
            # Upload via sftp
            sftp = self.create_sftp_connection()
            if remote_dir:
                # Make remote directories if needed.
                if not sftp.isdir(remote_dir):
                    sftp.makedirs(remote_dir)
                # Change to the remote directory before upload.
                sftp.chdir(remote_dir)
            LOGGER.debug(f"Uploading {file_name} to SFTP server")
            sftp.put(local_path)
            os.remove(local_path)
            sftp.close()

    def create_sftp_connection(self):
        """Pared-down adaptation of Local.create_sftp_connection"""
        connection_options = pysftp.CnOpts()
        connection_options.hostkeys = None
        return pysftp.Connection(**self.image_server.sftp_connection, cnopts=connection_options)

    def __list_sftp_files(self, pid):
        """Pared-down adaptation of Local.__list_sftp_files"""
        sftp = self.create_sftp_connection()
        remote_files = [remote_file for remote_file in sftp.listdir() if f"{pid}{self.image_server.path_delineator}" in remote_file]
        files = (
            [image for image in remote_files if "image" in guess_type(image)[0]],
            [ocr_file for ocr_file in remote_files if "image" not in guess_type(ocr_file)[0]],
        )
        sftp.close()
        return files

    @staticmethod
    def __file_info(path):
        """Pared-down adaptation of Local.__file_info"""
        return [
            path,
            path.split('/')[-1],
            guess_type(path)[0]
        ]