import requests
import json

from django.conf import settings
from apps.utils.fetch import fetch_url
import config.settings.local as local_settings


def get_canvas_info(canvas):
    """ Given a url, this function returns a dictionary of all collections."""
    results = fetch_url(canvas.service_id, timeout=settings.HTTP_REQUEST_TIMEOUT, format='json')
    return results

def add_positional_ocr(canvas):
    ocr = fetch_url("{p}{c}{s}".format(p=settings.DATASTREAM_PREFIX, c=canvas.pid.replace('fedora:',''), s=settings.DATASTREAM_SUFFIX), format='text/plain')
    return ocr
