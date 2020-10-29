""" Module of service classes and methods for ingest. """
import boto3

class UploadBundle:
    """ Class to negotiate file uploads """
    def __init__(self, canvas, file_path):
        """
        Class to upload images to a IIIF server's store.
        :param canvas: Canvas object being added.
        :type canvas: iiif.canvases.modesl.Canvas
        :param file_path: Path to image to be uploaded.
        :type file_path: str
        """
        self.canvas = canvas
        self.file = file_path
        self.s3_client = None

        if self.canvas.IIIF_IMAGE_SERVER_BASE.storage_service == 's3':
            self.s3_client = boto3.client('s3')

    def upload_bundle(self):
        """ Upload file to the given image server's store. """
        if self.s3_client is not None:
            self.s3_upload()

    def s3_upload(self):
        """ Upload file to S3 bucket. """
        self.s3_client.upload_file(
            self.file,
            self.canvas.IIIF_IMAGE_SERVER_BASE.storage_path,
            '{d}/{p}'.format(d=self.canvas.manifest.pid, p=self.canvas.pid)
        )
