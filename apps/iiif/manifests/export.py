from django.core.serializers import serialize
from .models import Manifest
from apps.iiif.annotations.models import Annotation
from datetime import datetime
import json
import zipfile
import io

class IiifManifestExport:
    @classmethod
    def get_zip(self, manifest, version):
        zip_subdir = manifest.label
        zip_filename = "iiif_export.zip"

        # Open BytesIO to grab in-memory ZIP contents
        byte_stream = io.BytesIO()

        # The zip compressor
        zf = zipfile.ZipFile(byte_stream, "w")

        # First write basic human-readable metadata
        title = manifest.label
        now = datetime.utcnow()
        readme = "Annotation export from Readux %(version)s\nExported at %(now)s UTC\nVolume: %(title)s\n" % locals()
        zf.writestr('README.txt', readme)

        # Next write the manifest
        zf.writestr('manifest.json',
            json.dumps(
                json.loads(
                    serialize(
                        'manifest',
                        [manifest],
                        version=version
                    )
                ),
                indent=4
            )
        )

        # Then write the annotations
        for canvas in manifest.canvas_set.all():
            if canvas.annotation_set.count() > 0:
                annotation_file = "annotation_list_" + canvas.pid + ".json"
                zf.writestr(
                    annotation_file,
                    json.dumps(
                        json.loads(
                            serialize(
                                'annotation_list',
                                [canvas],
                                version=version
                            )
                         ),
                        indent=4
                    )
                )

        zf.close() # flush zipfile to byte stream

        return byte_stream.getvalue()
