""" Model classes for ingesting volumes. """
import imghdr
import os
import uuid
import logging
import httpretty
from boto3 import client, resource
from io import BytesIO
from urllib.parse import urlparse, unquote
from mimetypes import guess_type
from shutil import rmtree
from tempfile import gettempdir, mkdtemp
from zipfile import ZipFile
from tablib import Dataset
from django.db import models
from django.conf import settings
from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.tasks import add_ocr_task
from apps.iiif.manifests.models import Manifest, ImageServer
import apps.ingest.services as services
from apps.utils.fetch import fetch_url
from .storages import IngestStorage

LOGGER = logging.getLogger(__name__)

def make_temp_file():
    """Creates a temporary directory.

    :return: Absolute path to the temporary directory
    :rtype: str
    """
    temp_file = mkdtemp()
    return temp_file

def bulk_path(instance, filename):
    return os.path.join('bulk', str(instance.bulk.id), filename )

class Bulk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

class Volume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bulk = models.ForeignKey(Bulk, on_delete=models.DO_NOTHING, null=False)
    volume_file = models.FileField(storage=IngestStorage(), upload_to=bulk_path)

class Local(models.Model):
    """ Model class for ingesting a volume from local files. """
    # temp_file_path = models.FilePathField(path=make_temp_file(), default=make_temp_file)
    bundle = models.FileField(blank=False, storage=IngestStorage())
    image_server = models.ForeignKey(ImageServer, on_delete=models.DO_NOTHING, null=True)
    manifest = models.ForeignKey(Manifest, on_delete=models.DO_NOTHING, null=True)
    local_bundle_path = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Local'

    @property
    def s3_client(self):
        if self.image_server.storage_service == 's3':
            return client('s3')
        return None

    @property
    def bucket(self):
        s3 = resource('s3')
        return s3.Bucket(self.image_server.storage_path)

    @property
    def tmp_bucket(self):
        return resource('s3').Bucket('readux-ingest')


    @property
    def zip_ref(self):
        """Create a reference to the uploaded zip file.

        :return: zipfile.ZipFile object of uploaded
        :rtype: zipfile.ZipFile
        https://medium.com/@johnpaulhayes/how-extract-a-huge-zip-file-in-an-amazon-s3-bucket-by-using-aws-lambda-and-python-e32c6cf58f06
        """
        if self.local_bundle_path and os.path.exists(self.local_bundle_path):
            return ZipFile(self.local_bundle_path)
        if self.local_bundle_path:
            return self.__fallback_download()
        try:
            buffer = BytesIO(self.bundle.file.obj.get()['Body'].read())
            return ZipFile(buffer)
        except OverflowError:
            # TODO: Figure out how to test this.
            return self.__fallback_download()

    @property
    def metadata(self):
        """
        Extract metadata from file.
        :return: If metadata file exists, returns the values. If no file, returns None.
        :rtype: dict or None
        """
        metadata = None
        for file in self.zip_ref.infolist():
            if 'metadata' in file.filename.casefold():

                if file.is_dir():
                    continue
                if metadata is not None:
                    continue
                if self.__is_junk(file.filename):
                    continue
                if 'ocr' in file.filename.casefold():
                    continue
                if 'image' in file.filename.casefold():
                    continue

                if 'csv' in guess_type(file.filename)[0] or 'tab-separated' in guess_type(file.filename)[0]:
                    data = self.zip_ref.read(file.filename)
                    metadata = Dataset().load(data.decode('utf-8-sig'))
                else:
                    metadata = Dataset().load(self.zip_ref.read(file.filename))

                if metadata is not None:
                    metadata = services.clean_metadata(metadata.dict[0])

                return metadata

    def extract_images_s3(self):
        """
        Extract image files directly to S3
        """
        if self.s3_client is None:
            return

        for filename in self.zip_ref.namelist():
            if self.__is_junk(filename):
                continue
            type = guess_type(filename)[0]
            if type is not None and 'image' in type:
                # TODO: check if file already exists in S3.
                # If it does, compare the hash and the S3 etag.
                # Don't upload if files are the same.
                self.s3_client.upload_fileobj(
                    self.zip_ref.open(filename),
                    Bucket=self.image_server.storage_path,
                    Key='{p}/{f}'.format(p=self.manifest.pid, f=filename.split("/")[-1].replace('_', '-'))
                )

    def extract_ocr_s3(self):
        """
        Locate and extract OCR files directly to S3
        """
        if self.s3_client is None:
            return

        for file in self.zip_ref.infolist():
            if 'ocr' not in file.filename.casefold():
                continue
            if 'metadata.' in file.filename:
                # The metadata file could slip through.
                # It's unlikely and will not hurt anything.
                continue
            if file.is_dir():
                continue
            if self.__is_junk(file.filename):
                continue
            type = guess_type(file.filename)[0]
            if type is not None and 'text' in type:
                self.s3_client.upload_fileobj(
                    self.zip_ref.open(file.filename),
                    Bucket=self.image_server.storage_path,
                    Key='{p}/_*ocr*_/{f}'.format(p=self.manifest.pid, f=file.filename.split("/")[-1].replace('_', '-'))
                )

    def create_canvases(self):
        """
        Create Canvas objects for each image file.
        """
        self.extract_images_s3()
        self.extract_ocr_s3()

        image_files = [
            file.key for file in self.bucket.objects.filter(Prefix=self.manifest.pid) if '_*ocr*_' not in file.key
        ]

        if len(image_files) == 0:
            # TODO: Throw an error here?
            pass
        ocr_files = [
            file.key for file in self.bucket.objects.filter(Prefix=self.manifest.pid) if '_*ocr*_' in file.key
        ]

        for index, key in enumerate(sorted(image_files)):
            image_file = key.split('/')[-1]

            LOGGER.debug(f'Creating canvas from {image_file}')

            ocr_file_path = None
            if len(ocr_files) > 0:
                image_name = '.'.join(image_file.split('.')[:-1])

                try:
                    ocr_key = [key for key in ocr_files if image_name in key][0]
                    ocr_file_path = f'https://readux.s3.amazonaws.com/{ocr_key}'
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
                    add_ocr_task.s(canvas.id)

        if self.manifest.canvas_set.count() == len(image_files):
            self.clean_up()
        else:
            # TODO: Log or though an error/waring?
            pass

    def clean_up(self):
        """ Method to clean up all the files. """
        if self.local_bundle_path and os.path.exists(self.local_bundle_path):
            os.remove(self.local_bundle_path)

        self.delete()

    @staticmethod
    def __is_junk(path):
        file = path.split('/')[-1]
        return file.startswith('.') or file.startswith('~') or file.startswith('__')

    def __fallback_download(self):
        self.local_bundle_path = os.path.join(
            gettempdir(),
            self.bundle.file.obj.key.split('/')[-1]
        )

        if os.path.isfile(self.local_bundle_path) is False:
            self.bundle.file.obj.download_file(self.local_bundle_path)
            self.save()

        return ZipFile(self.local_bundle_path)

class Remote(models.Model):
    """ Model class for ingesting a volume from remote manifest. """
    remote_url = models.CharField(max_length=255)
    manifest = models.ForeignKey(Manifest, on_delete=models.DO_NOTHING, null=True)

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

    @property
    def metadata(self):
        """ Take a remote IIIF manifest and create a derivative version. """
        if self.remote_manifest['@context'] == 'http://iiif.io/api/presentation/2/context.json':
            return services.parse_iiif_v2_manifest(self.remote_manifest)

        return None

    def create_canvases(self):
        for _ in range(20):
            print(len(self.remote_manifest['sequences'][0]['canvases']))
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
