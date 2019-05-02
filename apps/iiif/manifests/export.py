from django.core.serializers import serialize
from .models import Manifest
from apps.iiif.annotations.models import Annotation
import json
import zipfile
import io

# TODO Would still be nice to use DRF. Try this?
# https://stackoverflow.com/a/35019122
class IiifManifestExport:
    @classmethod
    def get_zip(self, manifest, version):
        zip_subdir = manifest.label
        zip_filename = "iiif_export.zip"

        # Open BytesIO to grab in-memory ZIP contents
        byte_stream = io.BytesIO()

        # The zip compressor
        zf = zipfile.ZipFile(byte_stream, "w")

        zf.writestr('test.txt', 'test contents')
        zf.writestr('manifest.json',
            serialize(
                'manifest',
                [manifest],
                version=version
            )
        )

        for canvas in manifest.canvas_set.all():
            annotation_file = "annotation_list_" + canvas.pid + ".json"
            zf.writestr(
                annotation_file,
                serialize(
                    'annotation_list',
                    [canvas],
                    version=version
                )
            )

        zf.close() # flush zipfile to byte stream

        return byte_stream.getvalue()
