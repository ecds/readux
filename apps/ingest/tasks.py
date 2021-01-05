""" Background task for creating canvases for ingest. """
from os import listdir, path, remove
from background_task import background
from apps.iiif.canvases.models import Canvas
from .services import UploadBundle

# pylint: disable=too-many-arguments
# There are so many arguments because background tasks can't take objects as arguments.
# All arguments "must all be serializable as JSON."
# @background(schedule=1)
# def create_canvas_task(
#     manifest_id, image_server_id, image_file_name, image_file_path, position, ocr_file_path, is_testing=False
# ):
#     """Background task to create canvases and upload images.

#     :param manifest_id: Primary key for canvas' apps.iiif.manifest.models.Manifest
#     :type manifest_id: UUID
#     :param image_server_id: Primary key for canvas' apps.iiif.canvases.models.IServer
#     :type image_server_id: UUID
#     :param image_file_name: Image's file name
#     :type image_file_name: str
#     :param image_file_path: Absolute path to the image file.
#     :type image_file_path: str
#     :param position: Canvas' position in volume's page order
#     :type position: int
#     :param ocr_file_path: Absolute path to the OCR file
#     :type ocr_file_path: str
#     """
#     manifest = Manifest.objects.get(pk=manifest_id)
#     image_server = IServer.objects.get(pk=image_server_id)
#     canvas = Canvas(
#         manifest=manifest,
#         pid='{m}_{f}'.format(m=manifest.pid, f=image_file_name),
#         IIIF_IMAGE_SERVER_BASE=image_server,
#         ocr_file_path=ocr_file_path,
#         position=position
#     )
#     if not is_testing:
#         upload = UploadBundle(canvas, image_file_path)
#         upload.upload_bundle()
#     canvas.save()
#     remove(image_file_path)
#     remove(ocr_file_path)
#     return canvas

@background(schedule=1)
def create_canvas_task(ingest, is_testing=False):
    """Background task to create canvases and upload images.

    :param ingest: Files to be ingested
    :type ingest: apps.ingest.models.local
    """
    # manifest = Manifest.objects.get(pk=manifest_id)
    # image_server = IServer.objects.get(pk=image_server_id)

    for index, image_file in enumerate(sorted(listdir(ingest.image_directory))):
        ocr_file_name = [
            f for f in listdir(ingest.ocr_directory) if f.startswith(image_file.split('.')[0])
        ][0]

        # Set up a background task to create the canvas.
        # create_canvas_task(
        #     manifest_id=ingest.manifest.id,
        #     image_server_id=ingest.image_server.id,
        #     image_file_name=image_file,
        # )
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
        # return canvas

    ingest.clean_up()
