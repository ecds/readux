from django.core.serializers import serialize
from .models import Manifest
from apps.iiif.annotations.models import Annotation
from datetime import datetime
from apps.users.models import User
import json
import zipfile
import io
import config.settings.local as settings

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
        ''' Annotated edition from {grab site identity/version of Readux} at {grab site URL}
        volume title
        volume author
        volume date
        volume publisher
        number of pages
        annotator username
        time of export
        '''
        title = manifest.label
        author = manifest.author
        date = manifest.published_date
        publisher = manifest.publisher
        page_count = manifest.canvas_set.count()
        now = datetime.utcnow()
        readux_url = settings.HOSTNAME
        #annotations = Annotation.objects.filter(canvas__manifest__id=manifest.id)
        annotators = User.objects.filter(annotation__canvas__manifest__id=manifest.id).distinct()
        annotators_string = ', '.join([str(i.name) for i in annotators])
        annotators_string = "Annotated by: " + annotators_string +"\n\n"
        # get the owner_id for each/all annotations
        # dedup the list of owners (although -- how to order?  alphabetical or by contribution count or ignore order)  .distinct()
        # turn the list of owners into a comma separated string of formal names instead of user ids
        readme = "Annotation export from Readux %(version)s at %(readux_url)s\nedition type: Readux IIIF Exported Edition\nexport date: %(now)s UTC\n\n" % locals()
        volume_data = "volume title: %(title)s\nvolume author: %(author)s\nvolume date: %(date)s\nvolume publisher: %(publisher)s\npages: %(page_count)s \n" % locals()
        boilerplate = "Readux is a platform developed by Emory University’s Center for Digital Scholarship for browsing, annotating, and publishing with digitized books. This zip file includes an International Image Interoperability Framework (IIIF) manifest for the digitized book and an annotation list for each page that includes both the encoded text of the book and annotations created by the user who created this export. This bundle can be used to archive the recognized text and annotations for preservation and future access.\n\n"
        explanation = "Each canvas (\"sc:Canvas\") in the manifest represents a page of the work. Each canvas includes an \"otherContent\" field-set with information identifying that page's annotation list. This field-set includes an \"@id\" field and the label field (\"@type\") \"sc:AnnotationList\". The \"@id\" field contains the URL link at which the annotation list was created and originally hosted from the Readux site. In order to host this IIIF manifest and its annotation lists again to browse the book and annotations outside of Readux, these @id fields would need to be updated to the appropriate URLs for the annotation lists on the new host."
        readme = readme + volume_data + annotators_string + boilerplate + explanation 
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
