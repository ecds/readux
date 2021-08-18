""" Module of service classes and methods for ingest. """
from urllib.parse import urlparse
from uuid import uuid4
import boto3
from django.apps import apps
from apps.iiif.manifests.models import Manifest
from apps.iiif.manifests.models import Manifest, RelatedLink


# class UploadBundle:
#     """ Class to negotiate file uploads """
#     def __init__(self, canvas, file_path):
#         """
#         Class to upload images to a IIIF server's store.
#         :param canvas: Canvas object being added.
#         :type canvas: iiif.canvases.modesl.Canvas
#         :param file_path: Path to image to be uploaded.
#         :type file_path: str
#         """
#         self.canvas = canvas
#         self.file = file_path
#         self.s3_client = None

#         if self.canvas.manifest.image_server.storage_service == 's3':
#             self.s3_client = boto3.client('s3')

#     def upload_bundle(self):
#         """ Upload file to the given image server's store. """
#         if self.s3_client is not None:
#             self.s3_upload()
#         else:
#             # TODO: How should this work?
#             pass

#     def s3_upload(self):
#         """ Upload file to S3 bucket. """
#         self.s3_client.upload_file(
#             self.file,
#             self.canvas.manifest.image_server.storage_path,
#             '{d}/{p}'.format(d=self.canvas.manifest.pid, p=self.file.split('/')[-1])
#         )

def clean_metadata(metadata):
    """Remove keys that do not aligin with Manifest fields.

    :param metadata:
    :type metadata: tablib.Dataset
    :return: Dictionary with keys matching Manifest fields
    :rtype: dict
    """
    metadata = {k.casefold().replace(' ', '_'): v for k, v in metadata.items()}
    fields = [f.name for f in Manifest._meta.get_fields()]
    invalid_keys = []

    for key in metadata.keys():
        if key not in fields:
            invalid_keys.append(key)

    for invalid_key in invalid_keys:
        metadata.pop(invalid_key)

    return metadata

def create_manifest(ingest):
    """
    Create or update a Manifest from supplied metadata and images.
    :return: New or updated Manifest with supplied `pid`
    :rtype: iiif.manifest.models.Manifest
    """
    manifest = None
    # Make a copy of the metadata so we don't extract it over and over.
    metadata = ingest.metadata
    if metadata is not None:
        manifest, created = Manifest.objects.get_or_create(pid=metadata['pid'].replace('_', '-'))
        for (key, value) in metadata.items():
            setattr(manifest, key, value)
        if not created:
            manifest.canvas_set.all().delete()
    else:
        manifest = Manifest(pid=str(uuid4()))

    manifest.image_server = ingest.image_server
    manifest.save()

    # This was giving me a 'django.core.exceptions.AppRegistryNotReady: Models aren't loaded yet' error.
    # Remote = apps.get_model('ingest.remote')
    # if type(ingest, .models.Remote):
    if type(ingest) == 'apps.ingest.model.Local':
        RelatedLink(
            manifest=manifest,
            link=ingest.remote_url,
            format='application/ld+json'
        ).save()

    return manifest

def extract_image_server(canvas):
    """Determins the IIIF image server URL for a given IIIF Canvas

    :param canvas: IIIF Canvas
    :type canvas: dict
    :return: IIIF image server URL
    :rtype: str
    """
    url = urlparse(canvas['images'][0]['resource']['service']['@id'])
    parts = url.path.split('/')
    parts.pop()
    base_path = '/'.join(parts)
    host = url.hostname
    if url.port is not None:
        host = '{h}:{p}'.format(h=url.hostname, p=url.port)
    return '{s}://{h}{p}'.format(s=url.scheme, h=host, p=base_path)
