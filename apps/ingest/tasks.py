""" Background task for creating canvases for ingest. """
from os import listdir, path, remove
from background_task import background
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.models import Manifest
from .services import UploadBundle
from apps.utils.fetch import fetch_url
from urllib.parse import urlparse

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
    manifest = Manifest.objects.get(pk=manifest_id)
    image_server = IServer.objects.get(pk=image_server_id)
    canvas = Canvas(
        manifest=manifest,
        pid='{m}_{f}'.format(m=manifest.pid, f=image_file_name),
        IIIF_IMAGE_SERVER_BASE=image_server,
        ocr_file_path=ocr_file_path,
        position=position
    )
    if not is_testing:
        upload = UploadBundle(canvas, image_file_path)
        upload.upload_bundle()
    canvas.save()
    remove(image_file_path)
    remove(ocr_file_path)
    return canvas

# @background(schedule=1)
# def create_canvas_task(ingest, is_testing=False):
#     """Background task to create canvases and upload images.

#     :param ingest: Files to be ingested
#     :type ingest: apps.ingest.models.local
#     """
#     manifest = Manifest.objects.get(pk=ingest['manifest_id'])
#     image_server = IServer.objects.get(pk=ingest['image_server_id'])

#     for index, image_file in enumerate(sorted(listdir(ingest['image_directory']))):
#         ocr_file_name = [
#             f for f in listdir(ingest['ocr_directory']) if f.startswith(image_file.split('.')[0])
#         ][0]

#         # Set up a background task to create the canvas.
#         # create_canvas_task(
#         #     manifest_id=ingest.manifest.id,
#         #     image_server_id=ingest.image_server.id,
#         #     image_file_name=image_file,
#         # )
#         image_file_path = path.join(ingest['image_directory'], image_file)
#         position = index + 1
#         ocr_file_path = path.join(ingest['temp_file_path'], ingest['ocr_directory'], ocr_file_name)

#         canvas = Canvas(
#             manifest=manifest,
#             pid='{m}_{f}'.format(m=manifest.pid, f=image_file),
#             IIIF_IMAGE_SERVER_BASE=image_server,
#             ocr_file_path=ocr_file_path,
#             position=position
#         )
#         if not is_testing:
#             upload = UploadBundle(canvas, image_file_path)
#             upload.upload_bundle()
#         canvas.save()
#         remove(image_file_path)
#         remove(ocr_file_path)
        # return canvas

    ingest.clean_up()

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
        # attributes = {k.casefold().replace(' ', '_'): v for k, v in metadata.dict[0].items()}
        # fields = [f.name for f in Manifest._meta.get_fields()]
        # invalid_keys = []
        # for key in attributes.keys():
        #     if key not in fields:
        #         invalid_keys.append(key)

        # for key in invalid_keys:
        #     attributes.pop(key)

        # for prop in metadata.headers:
        #     label = prop.casefold()
        #     value = metadata[prop][0]
            # pylint: disable=multiple-statements
            # I wish Python had switch statements.
            # if label == 'pid': attributes['pid'] = value
            # elif label == 'label': attributes['label'] = value
            # elif label == 'summary': attributes['summary'] = value
            # elif label == 'author': attributes['author'] = value
            # elif label == 'published city': attributes['published_city'] = value
            # elif label == 'published date': attributes['published_date'] = value
            # elif label == 'publisher': attributes['publisher'] = value
            # elif label == 'pdf': attributes['pdf'] = value
            # pylint: enable=multiple-statements
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
    metadata = {}
    url = urlparse(data['@id'])
    metadata['pid'] = '{h}-{i}'.format(h=url.hostname, i=url.path.split('/')[-2])
    metadata['label'] = data['label']
    metadata['summary'] = data['description']
    # for property in data['metadata']:

    return metadata

def create_derivative_manifest(remote):
    """ Take a remote IIIF manifest and create a derivative version. """
    data = fetch_url(remote.remote_url)
    extracted_data = None
    if data['@context'] == 'http://iiif.io/api/presentation/2/context.json':
        extracted_data = parse_iiif_v2_manifest(data)

    remote.manifest = Manifest()
