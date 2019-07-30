import requests
import json

from django.conf import settings
from apps.utils.fetch import fetch_url
import config.settings.local as local_settings


def get_canvas_info(canvas):
    """ Given a url, this function returns a dictionary of all collections."""
    return fetch_url(canvas.service_id, timeout=settings.HTTP_REQUEST_TIMEOUT, format='json')

def fetch_positional_ocr(canvas):
    if 'archivelab' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        return fetch_url("https://api.archivelab.org/books/{m}/pages/{p}/ocr?mode=words".format(m=canvas.manifest.pid, p=canvas.pid.split('$')[-1]))
    else:
        return fetch_url("{p}{c}{s}".format(p=settings.DATASTREAM_PREFIX, c=canvas.pid.replace('fedora:',''), s=settings.DATASTREAM_SUFFIX), format='text/plain')

def add_positional_ocr(canvas, result):
    ocr = []
    if 'archivelab' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        if 'ocr' in result and result['ocr'] is not None:
            for index, word in enumerate(result['ocr']):
                if len(word) > 0:
                    for w in word:
                        ocr.append({
                            'content': w[0],
                            'w': (w[1][2] - w[1][0]),
                            'h': (w[1][1] - w[1][3]),
                            'x': w[1][0],
                            'y': w[1][3] 
                        })
    else:
        if result is not None:
            # What comes back from fedora is 8-bit bytes
            for index, word in enumerate(result.decode('UTF-8-sig').strip().split('\r\n')):
                if (len(word.split('\t')) == 5):
                    ocr.append({
                        'content': word.split('\t')[4],
                        'w': int(word.split('\t')[2]),
                        'h': int(word.split('\t')[3]),
                        'x': int(word.split('\t')[0]),
                        'y': int(word.split('\t')[1])
                    })
    if (ocr):
        return ocr
    else:
        return None
