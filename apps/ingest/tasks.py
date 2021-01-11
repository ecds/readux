""" Common tasks for ingest. """
from os import listdir, path, remove
from background_task import background
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.models import Manifest
from urllib.parse import urlparse
from .services import UploadBundle
from apps.utils.fetch import fetch_url

@background(schedule=1)
def create_canvas_task(
    manifest_id, image_server_id, image_file_name, image_file_path, position, ocr_file_path, is_testing=False
):
    """Background task to create canvases and upload images.

    :param manifest_id: Primary key for canvas' apps.iiif.manifest.models.Manifest
    :type manifest_id: UUID
    :param image_server_id: Primary key for canvas' apps.iiif.canvases.models.IServer
    :type image_server_id: UUID
    :param image_file_name: Image's file name
    :type image_file_name: str
    :param image_file_path: Absolute path to the image file.
    :type image_file_path: str
    :param position: Canvas' position in volume's page order
    :type position: int
    :param ocr_file_path: Absolute path to the OCR file
    :type ocr_file_path: str
    """
    for index, image_file in enumerate(sorted(listdir(ingest.image_directory))):
        ocr_file_name = [
            f for f in listdir(ingest.ocr_directory) if f.startswith(image_file.split('.')[0])
        ][0]

        image_file_path = path.join(ingest.image_directory, image_file)
        position = index + 1
        ocr_file_path = path.join(ingest.temp_file_path, ingest.ocr_directory, ocr_file_name)

        canvas = Canvas(
            manifest=ingest.manifest,
            pid='{m}_{f}'.format(m=ingest.manifest.pid, f=image_file),
            IIIF_IMAGE_SERVER_BASE=ingest.image_server,
            ocr_file_path=ocr_file_path,
            position=position
        )
        if not is_testing:
            upload = UploadBundle(canvas, image_file_path)
            upload.upload_bundle()
        canvas.save()
        remove(image_file_path)
        remove(ocr_file_path)

    ingest.clean_up()

def create_remote_canvases(ingest):
    """Task to create Canavs objects from remote IIIF manifest

    :param ingest: Ingest model object
    :type ingest: apps.ingest.models.Remote
    """


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
        manifest, created = Manifest.objects.get_or_create(pid=metadata['pid'])
        for (key, value) in metadata.items():
            setattr(manifest, key, value)
        if created:
            manifest.canvas_set.all().delete()

    else:
        manifest = Manifest()

    manifest.save()
    return manifest

def parse_iiif_v2_manifest(data):
    """Parse IIIF Manifest based on v2.1.1 or the presentation API.
    https://iiif.io/api/presentation/2.1

    :param data: IIIF Presentation v2.1.1 manifest
    :type data: dict
    :return: Extracted metadata
    :rtype: dict
    """
    properties = {}
    for property in [{prop['label']: prop['value']} for prop in data['metadata']]:
        properties.update(property)
    manifest_data = [{prop: data[prop]} for prop in data if type(data[prop]) == str]
    for datum in manifest_data:
        properties.update(datum)
    properties['pid'] = urlparse(data['@id']).path.split('/')[-2]
    properties['summary'] = data['description']

    if 'logo' in properties:
        properties.pop('logo')

    manifest_metadata = clean_metadata(properties)
    manifest_metadata['image_server'] = __extract_image_server(data['sequences'][0]['canvases'][0])

    return manifest_metadata

def create_derivative_manifest(ingest):
    """ Take a remote IIIF manifest and create a derivative version. """
    data = fetch_url(ingest.remote_url)
    extracted_data = None
    if data['@context'] == 'http://iiif.io/api/presentation/2/context.json':
        extracted_data = parse_iiif_v2_manifest(data)

    setattr(ingest, 'metadata', extracted_data)

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

def __extract_image_server(canvas):
    url = urlparse(canvas['@id'])
    return '{s}://{h}/iiif'.format(s=url.scheme, h=url.hostname)
