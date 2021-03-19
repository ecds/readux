""" Model classes for ingesting volumes. """
import imghdr
import os
from urllib.parse import urlparse, quote, unquote
from mimetypes import guess_type
from shutil import rmtree
from tempfile import mkdtemp
from zipfile import ZipFile
from tablib import Dataset
from django.db import models
from apps.iiif.manifests.models import Manifest, ImageServer
import apps.ingest.services as services
from apps.utils.fetch import fetch_url

def make_temp_file():
    """Creates a temporary directory.

    :return: Absolute path to the temporary directory
    :rtype: str
    """
    temp_file = mkdtemp()
    return temp_file

class Local(models.Model):
    """ Model class for ingesting a volume from local files. """
    temp_file_path = models.FilePathField(path=make_temp_file(), default=make_temp_file)
    bundle = models.FileField(blank=False)
    image_server = models.ForeignKey(ImageServer, on_delete=models.DO_NOTHING, null=True)
    manifest = models.ForeignKey(Manifest, on_delete=models.DO_NOTHING, null=True)

    class Meta:
        verbose_name_plural = 'Local'

    @property
    def zip_ref(self):
        """Create a reference to the uploaded zip file.

        :return: zipfile.ZipFile object of uploaded
        :rtype: zipfile.ZipFile
        """
        return ZipFile(self.bundle.path)

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

        return dirs

    @property
    def image_directory(self):
        """Finds the absolute path to temporary directory containing image files.

        :return: Absolute path to temporary directory containing image files
        :rtype: str
        """
        path = None
        for file in self.zip_ref.namelist():
            if 'images' in file.casefold():
                self.zip_ref.extract(file, path=self.temp_file_path)
        for directory in self.bundle_dirs:
            if 'images/' in directory.filename.casefold():
                self.zip_ref.extract(directory, path=self.temp_file_path)
                path = os.path.join(self.temp_file_path, directory.filename)
        self.zip_ref.close()
        self.__remove_none_images(path)
        return path

    @property
    def ocr_directory(self):
        """Finds the absolute path to temporary directory containing OCR files.

        :return: Absolute path to temporary directory containing OCR files
        :rtype: str
        """
        path = None
        for file in self.zip_ref.namelist():
            if 'ocr' in file.casefold():
                self.zip_ref.extract(file, path=self.temp_file_path)
        for directory in self.bundle_dirs:
            if 'ocr/' in directory.filename.casefold():
                path = os.path.join(self.temp_file_path, directory.filename)
        self.zip_ref.close()
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
        for file in self.zip_ref.namelist():
            if 'metadata' in file.casefold():
                self.zip_ref.extract(file, path=self.temp_file_path)

                meta_file = os.path.join(self.temp_file_path, file)

                if 'csv' in guess_type(meta_file)[0]:
                    with open(meta_file, 'r', encoding='utf-8-sig') as file:
                        metadata = Dataset().load(file)
                else:
                    with open(meta_file, 'rb') as file:
                        metadata = Dataset().load(file)

        if metadata is not None:
            metadata = services.clean_metadata(metadata.dict[0])

        return metadata

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

        if 'metadata' in data:
            for iiif_metadata in [{prop['label']: prop['value']} for prop in data['metadata']]:
                properties.update(iiif_metadata)

        manifest_data = [{prop: data[prop]} for prop in data if isinstance(data[prop], str)]

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
