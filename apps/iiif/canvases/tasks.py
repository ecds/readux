""" Common tasks for canvases. """
from celery import Celery
from django.apps import apps
from ..annotations.models import Annotation
from .models import Canvas
from .services import add_ocr_annotations, get_ocr
from django.conf import settings

# Use `apps.get_model` to avoid circular import error. Because the parameters used to
# create a background task have to be serializable, we can't just pass in the model object.
# Canvas = apps.get_model('canvases.canvas')

app = Celery('apps.ingest')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(name='adding_ocr_to_canvas', autoretry_for=(Canvas.DoesNotExist,), retry_backoff=5)
def add_ocr_task(canvas_id, *args, **kwargs):
    """Function for parsing and adding OCR."""
    canvas = Canvas.objects.get(pk=canvas_id)
    ocr = get_ocr(canvas)

    if ocr is not None:
        add_ocr_annotations(canvas, ocr)
