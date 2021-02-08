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
from .tasks import create_canvas_task

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
        :rtype: tablib.core.Dataset or None
        """
        for file in self.zip_ref.namelist():
            if 'metadata' in file.casefold():
                self.zip_ref.extract(file, path=self.temp_file_path)

                meta_file = os.path.join(self.temp_file_path, file)

                if 'csv' in guess_type(meta_file)[0]:
                    with open(meta_file, 'r', encoding='utf-8-sig') as file:
                        return Dataset().load(file)

                with open(meta_file, 'rb') as file:
                    return Dataset().load(file)

        return None

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

    def create_manifest(self):
        """
        Create or update a Manifest from supplied metadata and images.
        :return: New or updated Manifest with supplied `pid`
        :rtype: iiif.manifest.models.Manifest
        """
        manifest = None
        # Make a copy of the metadata so we don't extract it over and over.
        metadata = self.metadata
        if metadata is not None:
            attributes = {}
            for prop in metadata.headers:
                label = prop.casefold()
                value = metadata[prop][0]
                # pylint: disable=multiple-statements
                # I wish Python had switch statements.
                if label == 'pid': attributes['pid'] = value
                elif label == 'label': attributes['label'] = value
                elif label == 'summary': attributes['summary'] = value
                elif label == 'author': attributes['author'] = value
                elif label == 'published city': attributes['published_city'] = value
                elif label == 'published date': attributes['published_date'] = value
                elif label == 'publisher': attributes['publisher'] = value
                elif label == 'pdf': attributes['pdf'] = value
                # pylint: enable=multiple-statements
            manifest, created = Manifest.objects.get_or_create(pid=attributes['pid'])
            for (key, value) in attributes.items():
                setattr(manifest, key, value)
            if created:
                manifest.canvas_set.all().delete()

        else:
            manifest = Manifest()

        manifest.save()
        self.manifest = manifest

    def add_canvases(self):
        """
        Method to kick off a background task to create the apps.iiif.canvases.models.Canvas objects
        and upload the files to the IIIF server store.
        """
        if self.manifest is None:
            self.create_manifest()

        self_dict = self.__dict__
        self_dict['image_directory'] = self.image_directory
        self_dict['ocr_directory'] = self.ocr_directory

        create_canvas_task(
                manifest_id=self.manifest.id,
                image_server_id=self.image_server.id,
                image_file_name=image_file,
                image_file_path=os.path.join(self.image_directory, image_file),
                position=index + 1,
                ocr_file_path=os.path.join(self.temp_file_path, self.ocr_directory, ocr_file_name)
            )

    def clean_up(self):
        """ Method to clean up all the files. This is really only applicable for testing. """
        rmtree(self.temp_file_path)
        os.remove(self.bundle.path)
        self.delete()
