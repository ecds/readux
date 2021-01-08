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
            if 'ocr' in file.casefold() and '__MACOSX' not in file:
                self.zip_ref.extract(file, path=self.temp_file_path)
        for directory in self.bundle_dirs:
            if 'ocr/' in directory.filename.casefold() and '__MACOSX' not in directory.filename:
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
            if 'metadata' in file.casefold() and '__MACOSX' not in file:
                self.zip_ref.extract(file, path=self.temp_file_path)

                meta_file = os.path.join(self.temp_file_path, file)

                if 'csv' in guess_type(meta_file)[0]:
                    print('^^^^^^^^^^^^^^^^^^^^ ' + meta_file + ' ^^^^^^^^^^^^^^^^^^^^^^^^')
                    with open(meta_file, 'r', encoding='utf-8-sig') as file:
                        metadata = Dataset().load(file)
                else:
                    with open(meta_file, 'rb') as file:
                        metadata = Dataset().load(file)

        if metadata is not None:
            metadata = self.__clean_metadata(metadata)

        return metadata

    @staticmethod
    def __remove_none_images(path):
        print('***************')
        print(path)
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

    @staticmethod
    def __clean_metadata(metadata):
        """Remove keys that do not aligin with Manifest fields.

        :param metadata:
        :type metadata: tablib.Dataset
        :return: Dictionary with keys matching Manifest fields
        :rtype: dict
        """
        metadata = {k.casefold().replace(' ', '_'): v for k, v in metadata.dict[0].items()}
        fields = [f.name for f in Manifest._meta.get_fields()]
        invalid_keys = []

        for key in metadata.keys():
            if key not in fields:
                invalid_keys.append(key)

        for invalid_key in invalid_keys:
            metadata.pop(invalid_key)
        print(metadata)
        return metadata

    def add_canvases(self):
        """
        Method to kick off a background task to create the apps.iiif.canvases.models.Canvas objects
        and upload the files to the IIIF server store.
        """
        if self.manifest is None:
            self.manifest = tasks.create_manifest(self)

        tasks.create_canvas_task(self)

        # for index, image_file in enumerate(sorted(os.listdir(self.image_directory))):
        #     ocr_file_name = [
        #         f for f in os.listdir(self.ocr_directory) if f.startswith(image_file.split('.')[0])
        #     ][0]

        #     # Set up a background task to create the canvas.
        #     create_canvas_task(
        #         manifest_id=self.manifest.id,
        #         image_server_id=self.image_server.id,
        #         image_file_name=image_file,
        #         image_file_path=os.path.join(self.image_directory, image_file),
        #         position=index + 1,
        #         ocr_file_path=os.path.join(self.temp_file_path, self.ocr_directory, ocr_file_name)
        #     )

        # local.clean_up()

    def clean_up(self):
        """ Method to clean up all the files. This is really only applicable for testing. """
        rmtree(self.temp_file_path)
        os.remove(self.bundle.path)
        self.delete()

class Remote(models.Model):
    """ Model class for ingesting a volume from remote manifest. """
    remote_url = models.CharField(max_length=255)
    manifest = models.ForeignKey(Manifest, on_delete=models.DO_NOTHING, null=True)
