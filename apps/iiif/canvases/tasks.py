""" Common tasks for canvases. """
from background_task import background
from django.apps import apps
from ..annotations.models import Annotation
from .services import get_ocr

# Use `apps.get_model` to avoid circular import error. Because the parameters used to
# create a background task have to be serializable, we can't just pass in the model object.
Canvas = apps.get_model('canvases.canvas')

@background(schedule=5)
def add_ocr(canvas_id, *args, **kwargs):
    """Function for parsing and adding OCR."""
    canvas = Canvas.objects.get(pk=canvas_id)
    word_order = 1
    ocr = get_ocr(canvas)

    if ocr is not None:
        for word in ocr:
            # A quick check to make sure the header row didn't slip through.
            if word['x'] == 'x':
                continue

            # Set the content to a single space if it's missing.
            if (
                word == '' or
                'content' not in word or
                not word['content'] or
                word['content'].isspace()
            ):
                word['content'] = ' '
            anno = Annotation()
            anno.canvas = canvas
            anno.x = word['x']
            anno.y = word['y']
            anno.w = word['w']
            anno.h = word['h']
            anno.resource_type = anno.OCR
            anno.content = word['content']
            anno.order = word_order
            anno.save()
            word_order += 1