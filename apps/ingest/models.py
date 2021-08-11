""" Model classes for ingesting volumes. """
import imghdr
import os
import uuid
import logging
from boto3 import client, resource
from io import BytesIO
from urllib.parse import urlparse
from mimetypes import guess_type
from shutil import rmtree
from tempfile import mkdtemp
from zipfile import ZipFile
from tablib import Dataset
from storages.backends.s3boto3 import S3Boto3Storage
from django.db import models
from apps.iiif.manifests.models import Manifest, ImageServer
import apps.ingest.services as services
from apps.utils.fetch import fetch_url
from apps.ingest.storages import TmpStorage

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
    volume_file = models.FileField(storage=TmpStorage(), upload_to=bulk_path)

class Local(models.Model):
    """ Model class for ingesting a volume from local files. """
    temp_file_path = models.FilePathField(path=make_temp_file(), default=make_temp_file)
    bundle = models.FileField(blank=False, storage=TmpStorage())
    image_server = models.ForeignKey(ImageServer, on_delete=models.DO_NOTHING, null=True)
    manifest = models.ForeignKey(Manifest, on_delete=models.DO_NOTHING, null=True)

    class Meta:
        verbose_name_plural = 'Local'

    @property
    def s3_client(self):
        if self.image_server.storage_service == 's3':
            return client('s3')
        return None

    @property
    def zip_ref(self):
        """Create a reference to the uploaded zip file.

        :return: zipfile.ZipFile object of uploaded
        :rtype: zipfile.ZipFile
        """
        # return ZipFile(self.bundle.path)
        # s3_resource = resource('s3')
        # zip_obj = s3_resource.Object(bucket_name='readux', key=self.bundle.path)
        buffer = BytesIO(self.bundle.file.obj.get()['Body'].read())
        return ZipFile(buffer)

    @property
    def bundle_dirs(self):
        """
        Find all the directories in the uploaded zip
        :return: List of directories in uploaded zip
        :rtype: list
        """
        dirs = []
        for item in self.zip_ref.infolist():
            # pylint: disable=expression-not-assigned
            dirs.append(item) if item.is_dir() else None
            # pylint: enable=expression-not-assigned
        if not dirs and all(not item.is_dir() for item in self.zip_ref.infolist()):
            dirs.extend([i for i in self.zip_ref.infolist() if 'ocr' in i.filename])
            dirs.extend([i for i in self.zip_ref.infolist() if 'images' in i.filename])

        return dirs

    @staticmethod
    def upload_images_s3(self):
        if self.s3_client is None:
            return

        for filename in self.zip_ref.namelist():
            # file_info = self.zip_ref.getinfo(filename)
            type = guess_type(filename)[0]
            if type is not None and 'image' in type:
                self.s3_client.upload_fileobj(
                    self.zip_ref.open(filename),
                    Bucket=self.image_server.storage_path,
                    Key='{p}/{f}'.format(p=self.manifest.pid, f=filename.split("/")[-1])
                )

    @staticmethod
    def upload_ocr_s3(self):
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
                    Key='{p}/_*ocr*_/{f}'.format(p=self.manifest.pid, f=file.filename.split("/")[-1])
                )

    @property
    def image_directory(self):
        """Finds the absolute path to temporary directory containing image files.

        :return: Absolute path to temporary directory containing image files
        :rtype: str
        https://medium.com/@johnpaulhayes/how-extract-a-huge-zip-file-in-an-amazon-s3-bucket-by-using-aws-lambda-and-python-e32c6cf58f06
        for filename in z.namelist():
            file_info = z.getinfo(filename)
            type = guess_type(filename)[0]
            if type is not None and 'image' in type:
                client.upload_fileobj(z.open(filename), Bucket='readux', Key='testtesttest/{f}'.format(f=filename.split("/")[-
        ...: 1]))

        client.put_object_tagging(Bucket='readux', Key='00000005.jp2', Tagging={'TagSet': [{'Key': 'poop', 'Value': 'head'}]})

        buffer = BytesIO(zip_obj.get()['Body'].read())
        z = ZipFile(buffer)
        for file in z.namelist():
            if 'meta' in file:
            metadata = z.read(file)

        data = Dataset().load(metadata)
        """
        path = None
        for file in self.zip_ref.namelist():
            if 'images' in file.casefold():
                self.zip_ref.extract(file, path=self.temp_file_path)
        for directory in self.bundle_dirs:
            if 'images/' in directory.filename.casefold():
                self.zip_ref.extract(directory, path=self.temp_file_path)
                if directory.is_dir():
                    path = os.path.join(self.temp_file_path, directory.filename)
                else:
                    path = os.path.join(
                        self.temp_file_path,
                        f"{directory.filename.split('images')[0]}images"
                    )
        self.zip_ref.close()
        self.__remove_junk(path)
        self.__remove_underscores(path)
        self.__remove_none_images(path)
        return path

    @property
    def ocr_directory(self):
        """
        Finds the absolute path to temporary directory containing OCR files.

        :return: Absolute path to temporary directory containing OCR files
        :rtype: str
        """
        path = None
        for file in self.zip_ref.namelist():
            if 'ocr' in file.casefold():
                self.zip_ref.extract(file, path=self.temp_file_path)
        for directory in self.bundle_dirs:
            if 'ocr/' in directory.filename.casefold():
                if directory.is_dir():
                    path = os.path.join(self.temp_file_path, directory.filename)
                else:
                    path = os.path.join(
                        self.temp_file_path,
                        f"{directory.filename.split('ocr')[0]}ocr"
                    )
        self.zip_ref.close()
        self.__remove_junk(path)
        self.__remove_underscores(path)
        self.__remove_none_text_files(path)
        return path

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
                    metadata = Dataset().load(data.decode('utf-8'))
                else:
                    metadata = Dataset().load(self.zip_ref.read(file.filename))

                if metadata is not None:
                    metadata = services.clean_metadata(metadata.dict[0])

                return metadata

    @staticmethod
    def __is_junk(path):
        file = path.split('/')[-1]
        return file.startswith('.') or file.startswith('~') or file.startswith('__')

    @staticmethod
    def __remove_junk(path):
        for junk in [f for f in os.listdir(path) if f.startswith('.')]:
            junk_file = os.path.join(path, junk)
            if os.path.isdir(junk_file):
                rmtree(junk_file)
            else:
                os.remove(junk_file)
        # for junk in [f for f in os.listdir(path) if f.startswith('_') and os.path.isdir(f)]:
        #     rmtree(junk)

    @staticmethod
    def __remove_underscores(path):
        for file in [f for f in os.listdir(path) if '_' in f]:
            os.rename(os.path.join(path, file), os.path.join(path, file.replace('_', '-')))

    @staticmethod
    def __remove_none_images(path):
        for image_file in os.listdir(path):
            image_file_path = os.path.join(path, image_file)
            if imghdr.what(image_file_path) is None:
                if os.path.isdir(image_file_path):
                    rmtree(image_file_path)
                else:
                    os.remove(image_file_path)

    @staticmethod
    def __remove_none_text_files(path):
        for ocr_file in os.listdir(path):
            ocr_file_path = os.path.join(path, ocr_file)
            if 'text' not in guess_type(ocr_file_path)[0]:
                if os.path.isdir(ocr_file_path):
                    rmtree(ocr_file_path)
                else:
                    os.remove(ocr_file_path)

    def clean_up(self):
        """ Method to clean up all the files. This is really only applicable for testing. """
        rmtree(self.temp_file_path)
        os.remove(self.bundle.path)
        self.delete()

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
        return fetch_url(self.remote_url)

    @property
    def metadata(self):
        """ Take a remote IIIF manifest and create a derivative version. """
        if self.remote_manifest['@context'] == 'http://iiif.io/api/presentation/2/context.json':
            return self.__parse_iiif_v2_manifest(self.remote_manifest)

        return None

    @staticmethod
    def __parse_iiif_v2_manifest(data):
        """Parse IIIF Manifest based on v2.1.1 or the presentation API.
        https://iiif.io/api/presentation/2.1

        :param data: IIIF Presentation v2.1.1 manifest
        :type data: dict
        :return: Extracted metadata
        :rtype: dict
        """
        properties = {}
        manifest_data = []

        if 'metadata' in data:
            manifest_data.append({ 'metadata': data['metadata'] })

            for iiif_metadata in [{prop['label']: prop['value']} for prop in data['metadata']]:
                properties.update(iiif_metadata)

        # Sometimes, that label appears as a list.
        if 'label' in data.keys() and isinstance(data['label'], list):
            data['label'] = ' '.join(data['label'])

        manifest_data.extend([{prop: data[prop]} for prop in data if isinstance(data[prop], str)])

        for datum in manifest_data:
            properties.update(datum)

        properties['pid'] = urlparse(data['@id']).path.split('/')[-2]
        properties['summary'] = data['description'] if 'description' in data else ''

        # TODO: Work out adding remote logos
        if 'logo' in properties:
            properties.pop('logo')

        manifest_metadata = services.clean_metadata(properties)

        return manifest_metadata

    # @staticmethod
    # def parse_iiif_v2_canvas(canvas):
    #     id_uri = urlparse(unquote(canvas['@id']))
    #     service = urlparse(unquote(canvas['images'][0]['service']['@id']))
    #     resource_id = service.path.split('/').pop()
    #     return {
    #         'pid': canvas['@id'].split('/')[-2],
    #         'resource_id': quote(resource_id, save='')
    #     }
