""" Model classes for ingesting volumes. """
import imghdr
import os
# from bagit import Bag
from mimetypes import guess_type
from shutil import rmtree
from tempfile import mkdtemp
from zipfile import ZipFile
from tablib import Dataset
from django.db import models
from apps.utils.fetch import fetch_url
from apps.iiif.manifests.models import Manifest
from apps.iiif.canvases.models import IServer
import apps.ingest.tasks as tasks

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
    image_server = models.ForeignKey(IServer, on_delete=models.DO_NOTHING, null=True)
    manifest = models.ForeignKey(Manifest, on_delete=models.DO_NOTHING, null=True)

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
            metadata = tasks.clean_metadata(metadata.dict[0])

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

    def add_canvases(self):
        """
        Method to kick off a background task to create the apps.iiif.canvases.models.Canvas objects
        and upload the files to the IIIF server store.
        """
        if self.manifest is None:
            self.manifest = tasks.create_manifest(self)

        tasks.create_canvas_task(self)

    def clean_up(self):
        """ Method to clean up all the files. This is really only applicable for testing. """
        rmtree(self.temp_file_path)
        os.remove(self.bundle.path)
        self.delete()

class Remote(models.Model):
    """ Model class for ingesting a volume from remote manifest. """
    remote_url = models.CharField(max_length=255)
    manifest = models.ForeignKey(Manifest, on_delete=models.DO_NOTHING, null=True)

    @property
    def metadata(self):
        """ Holder for Manifest metadata.

        :return: Extracted metadata from from remote manifest
        :rtype: dict
        """
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        """ Setter for self.metadata """
        self._metadata = value

# from apps.ingest.tasks import create_derivative_manifest
# remote = Remote()
# remote.remote_url = 'https://iiif.archivelab.org/iiif/09359080.4757.emory.edu/manifest.json'
# create_derivative_manifest(remote)