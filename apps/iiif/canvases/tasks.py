""" Common tasks for canvases. """
from celery import Celery
from .models import Canvas
from .services import add_ocr_annotations, get_ocr, add_oa_annotations
from django.conf import settings

app = Celery('apps.iiif.canvases')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(name='adding_ocr_to_canvas', autoretry_for=(Canvas.DoesNotExist,), retry_backoff=5)
def add_ocr_task(canvas_id, *args, **kwargs):
    """Function for parsing and adding OCR."""
    canvas = Canvas.objects.get(pk=canvas_id)
    ocr = get_ocr(canvas)

    if ocr is not None:
        add_ocr_annotations(canvas, ocr)
        canvas.save()  # trigger reindex

@app.task(name='adding_oa_ocr_to_canvas', retry_backoff=5)
def add_oa_ocr_task(annotation_list_url):
    add_oa_annotations(annotation_list_url)
