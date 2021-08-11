# pylint: disable = unused-argument

""" Common tasks for ingest. """
import logging
from os import listdir, path
from uuid import uuid4
from urllib.parse import urlparse, unquote
from celery import Celery
from boto3 import resource
from botocore.exceptions import ClientError
from background_task import background
from django.apps import apps
from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.tasks import add_ocr, add_ocr_task
from apps.iiif.manifests.models import Manifest, RelatedLink
from .services import UploadBundle
from django.conf import settings

# Use `apps.get_model` to avoid circular import error. Because the parameters used to
# create a background task have to be serializable, we can't just pass in the model object.
Local = apps.get_model('ingest.local') # pylint: disable = invalid-name
Remote = apps.get_model('ingest.remote')

LOGGER = logging.getLogger(__name__)
logging.getLogger("background_task").setLevel(logging.ERROR)
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('nose').setLevel(logging.CRITICAL)
logging.getLogger('s3transfer').setLevel(logging.CRITICAL)

app = Celery('apps.ingest')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(name='creating_canvases_from_local', autoretry_for=(Local.DoesNotExist,), retry_backoff=5)
def create_canvas_form_local_task(ingest_id):
    ingest = Local.objects.get(pk=ingest_id)
    if ingest.manifest is None:
        ingest.manifest = create_manifest(ingest)
        ingest.save()
        ingest.refresh_from_db()
    ingest.upload_images_s3(ingest)
    ingest.upload_ocr_s3(ingest)
    s3 = resource('s3')
    bucket = s3.Bucket('readux')
    LOGGER.debug('^^^^^ hmmmmmmm')

    # try:
    #     s3.Object('readux', ingest.manifest.pid).load()
    # except ClientError as error:
    #     if error.response['Error']['Code'] == '404':
    #         LOGGER.debug('^^^^^ 404')
    #         pass
    # else:
    image_files = [
        file.key for file in bucket.objects.filter(Prefix=ingest.manifest.pid) if '_*ocr*_' not in file.key
    ]
    LOGGER.debug(f'^^^^^First image file {image_files[0]}')
    if len(image_files) == 0:
        # TODO: Throw an error here?
        pass
    ocr_files = [
        file.key for file in bucket.objects.filter(Prefix=ingest.manifest.pid) if '_*ocr*_' in file.key
    ]
    LOGGER.debug(f'^^^^^First ocr file {ocr_files[0]}')

    for index, key in enumerate(sorted(image_files)):
        image_file = key.split('/')[-1]
        LOGGER.debug(f'^^^^^Creating canvas from {image_file}')
        ocr_file_path = None
        if len(ocr_files) > 0:
            image_name = '.'.join(image_file.split('.')[:-1])
            LOGGER.debug(f'^^^^^IMAGE NAME {image_name}')
            try:
                ocr_key = [key for key in ocr_files if image_name in key][0]
                ocr_file_path = f'https://readux.s3.amazonaws.com/{ocr_key}'
            except IndexError:
                # Every image may not have a matching OCR file
                ocr_file_path = None
                pass
        position = index + 1
        canvas, created = Canvas.objects.get_or_create(
            manifest=ingest.manifest,
            pid=f'{ingest.manifest.pid}_{image_file}',
            ocr_file_path=ocr_file_path,
            position=position
        )

        if created and canvas.ocr_file_path is not None:
            add_ocr_task.delay(canvas.id)

# @background(schedule=1)
# @app.task(name='creating_canvases_from_local', autoretry_for=(Local.DoesNotExist,), retry_backoff=5)
def create_canvas_task(ingest_id, *args, is_testing=False, **kwargs):
    """Background task to create canvases and upload images.

    :param ingest_id: Primary key for .models.Local objects
    :type ingest_id: UUID

    :param is_testing: [description], defaults to False
    :type is_testing: bool, optional
    from botocore.exceptions import ClientError

    """
    pass
    # ingest = Local.objects.get(pk=ingest_id)

    # if path.isfile(ingest.bundle.path):
    #     for index, image_file in enumerate(sorted(listdir(ingest.image_directory))):
    #         LOGGER.debug(f'Creating canvas from {image_file}')
    #         position = index + 1
    #         ocr_file_name = [
    #             f for f in listdir(ingest.ocr_directory) if f.startswith(image_file.split('.')[0])
    #         ][0]

    #         image_file_path = path.join(ingest.image_directory, image_file)
    #         ocr_file_path = path.join(ingest.temp_file_path, ingest.ocr_directory, ocr_file_name)

    #         # The task will retry if there is an error. This prevents the creation of
    #         # multiple versions of the same canvas
    #         canvas, created = Canvas.objects.get_or_create(
    #             manifest=ingest.manifest,
    #             pid=f'{ingest.manifest.pid}_{image_file}',
    #             ocr_file_path=ocr_file_path,
    #             position=position
    #         )
    #         if created:
    #             if not is_testing:
    #                 upload_canvas.delay(canvas.id, image_file_path)
    #             # canvas.save()
    #             if is_testing:
    #                 add_ocr_task = add_ocr.now
    #                 add_ocr_task(canvas.id,
    #                     verbose_name=f'Adding OCR for {canvas.manifest.pid} page {canvas.position}'
    #                 )
    #             else:
    #                 add_ocr(
    #                     canvas.id,
    #                     verbose_name=f'Adding OCR for {canvas.manifest.pid} page {canvas.position}'
    #                 )

    # # Sometimes, the IIIF server is not ready to process the image by the time the canvas is saved to
    # # the database. As a double check loop through to make sure the height and width has been saved.
    # for canvas in ingest.manifest.canvas_set.all():
    #     if canvas.width == 0 or canvas.height == 0:
    #         canvas.save()

    # # Finally schedule a task clean up the files and the ingest object.
    # if is_testing:
    #     local_clean_up_task.now(ingest_id)
    # else:
    #     local_clean_up_task(ingest_id)

@app.task(name='uploading_canvases_from_local', autoretry_for=(Canvas.DoesNotExist,), retry_backoff=5)
def upload_canvas(canvas_id, image_file_path):
    canvas = Canvas.objects.get(id=canvas_id)
    upload = UploadBundle(canvas, image_file_path)
    upload.upload_bundle()


@background(schedule=1)
def create_remote_canvases(ingest_id, *args, **kwargs):
    """Task to create Canavs objects from remote IIIF manifest

    :param ingest_id: ID for ingest
    :type ingest: UUID
    """
    # Use `apps.ge_model` to avoid circular import error. Because the parameters used to
    # create a background task have to be serializable, we can't just pass in the model object.
    remote_ingest = Remote.objects.get(pk=ingest_id)

    if remote_ingest.manifest is None:
        remote_ingest.manifest = create_manifest(remote_ingest)
        remote_ingest.save()
        remote_ingest.refresh_from_db()

    # TODO: What if there are multiple sequences? Is that even allowed in IIIF?
    for position, canvas in enumerate(remote_ingest.remote_manifest['sequences'][0]['canvases']):
        canvas_metadata = None
        # TODO: we will need some sort of check for IIIF API version, but not
        # everyone includes a context for each canvas.
        # if canvas['@context'] == 'http://iiif.io/api/presentation/2/context.json':
        canvas_metadata = parse_iiif_v2_canvas(canvas)

        if canvas_metadata is not None:
            canvas, _created = Canvas.objects.get_or_create(
                pid=canvas_metadata['pid'],
                manifest=remote_ingest.manifest,
                position=position
            )

            for (key, value) in canvas_metadata.items():
                setattr(canvas, key, value)
            canvas.save()

    remote_ingest.delete()

# TODO: Maybe a better way to do this is mark an ingest as "done".
# Then, once a day, clean up all that are done.
@background(schedule=86400)
def local_clean_up_task(ingest_id, *args, **kwargs):
    """
    Scheduled a task to clean up ingest files from the local disk

    :param ingest_id: Primary key for an ingest object.
    :type ingest_id: int
    """
    ingest = Local.objects.get(pk=ingest_id)
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
        manifest, created = Manifest.objects.get_or_create(pid=metadata['pid'])
        for (key, value) in metadata.items():
            setattr(manifest, key, value)
        if not created:
            manifest.canvas_set.all().delete()
    else:
        manifest = Manifest(pid=str(uuid4()))

    manifest.image_server = ingest.image_server
    manifest.save()

    if isinstance(ingest, Remote):
        RelatedLink(
            manifest=manifest,
            link=ingest.remote_url,
            format='application/ld+json'
        ).save()

    return manifest

# TODO: I don't like this here while the manifest version is on the Remote model class.
def parse_iiif_v2_canvas(canvas):
    """ """
    canvas_id = canvas['@id'].split('/')
    pid = canvas_id[-1] if canvas_id[-1] != 'canvas' else canvas_id[-2]

    service = urlparse(canvas['images'][0]['resource']['service']['@id'])
    resource = unquote(service.path.split('/').pop())

    summary = canvas['description'] if 'description' in canvas.keys() else ''
    label = canvas['label'] if 'label' in canvas.keys() else ''
    return {
        'pid': pid,
        'height': canvas['height'],
        'width': canvas['width'],
        'summary': summary,
        'label': label,
        'resource': resource
    }

@app.task(name="sum_two_numbers")
def add(x, y):
    return x + y
