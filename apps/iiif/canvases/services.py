# pylint: disable=invalid-name
"""Module to provide some common functions for Canvas objects."""
import csv
from xml.etree import ElementTree
import httpretty
from django.conf import settings
from apps.utils.fetch import fetch_url

class IncludeQuotesDialect(csv.Dialect): # pylint: disable=too-few-public-methods
    """Subclass of csv.Dialect to include the quote marks in OCR content."""
    # include the quote marks in content
    lineterminator = '\n'
    delimiter = '\t'
    quoting = csv.QUOTE_NONE # perform no special processing of quote characters

@httpretty.activate
def get_fake_canvas_info(canvas):
    """Function to mock a response for testing.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :return: OCR data
    :rtype: requests.models.Response
    """
    with open('apps/iiif/canvases/fixtures/info.json', 'r') as file:
        iiif_image_info = file.read().replace('\n', '')
    httpretty.register_uri(httpretty.GET, canvas.service_id, body=iiif_image_info)
    response = fetch_url(canvas.service_id, timeout=settings.HTTP_REQUEST_TIMEOUT, format='json')
    return response

def get_fake_ocr():
    return [
        {
            "h": 22,
            "w": 22,
            "x": 1146,
            "y": 928,
            "content": "Dope"
        },
        {
            "h": 222,
            "w": 222,
            "x": 11462,
            "y": 9282,
            "content": ""
        },
        {
            "h": 21,
            "w": 21,
            "x": 1141,
            "y": 9281,
            "content": "southernplayalisticadillacmuzik"
        },
        {
            "h": 213,
            "w": 213,
            "x": 11413,
            "y": 92813
        },
        {
            "h": 214,
            "w": 214,
            "x": 11414,
            "y": 92814,
            "content": " "
        }
    ]

def get_ocr(canvas):
    """Function to determine method for fetching OCR for a canvas.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :return: List of dicts of parsed OCR data.
    :rtype: list
    """
    if 'fake.info' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        return get_fake_ocr()
    if canvas.default_ocr == "line":
        result = fetch_alto_ocr(canvas)
        return add_alto_ocr(result)
    result = fetch_positional_ocr(canvas)
    return add_positional_ocr(canvas, result)

def get_canvas_info(canvas):
    """Given a canvas, this function returns the IIIF image info.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :return: IIIF image info as JSON
    :rtype: requests.models.Response
    """
    # If testing, just fake it.
    if 'fake.info' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        return get_fake_canvas_info(canvas)

    return fetch_url(canvas.service_id, timeout=settings.HTTP_REQUEST_TIMEOUT, format='json')

# TODO: Maybe add "OCR Source" and "OCR Type" attributes to the manifest model. That might
# help make this more universal.
def fetch_positional_ocr(canvas):
    """Function to get OCR for a canvas depending on the image's source.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :return: Positional OCR data
    :rtype: requests.models.Response
    """
    if 'archivelab' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        return fetch_url(
            "https://api.archivelab.org/books/{m}/pages/{p}/ocr?mode=words".format(
                m=canvas.manifest.pid,
                p=str(int(canvas.pid.split('$')[-1]) - canvas.ocr_offset)
            )
        )
    if 'images.readux.ecds.emory' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        return fetch_url(
            "https://raw.githubusercontent.com/ecds/ocr-bucket/master/{m}/{p}.tsv".format(
                m=canvas.manifest.pid,
                p=canvas.pid.split('_')[-1]
                .replace('.jp2', '')
                .replace('.jpg', '')
                .replace('.tif', '')
            ),
            format='text'
        )
    return fetch_url(
        "{p}{c}{s}".format(
            p=settings.DATASTREAM_PREFIX,
            c=canvas.pid.replace('fedora:', ''),
            s=settings.DATASTREAM_SUFFIX), format='text/plain'
        )

def add_positional_ocr(canvas, result):
    """Function to parse fetched OCR data for a canvas.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :param result: Previously fetched OCR data
    :type result: requests.models.Response
    :return: List of dicts of parsed OCR data.
    :rtype: list
    """
    ocr = []
    if 'archivelab' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        if result is not None and 'ocr' in result and result['ocr'] is not None:
            for index, word in enumerate(result['ocr']): # pylint: disable=unused-variable
                if len(word) > 0:
                    for w in word:
                        ocr.append({
                            'content': w[0],
                            'w': (w[1][2] - w[1][0]),
                            'h': (w[1][1] - w[1][3]),
                            'x': w[1][0],
                            'y': w[1][3]
                        })
    elif 'images.readux.ecds.emory' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:

        reader = csv.DictReader(result.split('\n'), dialect=IncludeQuotesDialect)

        for row in reader:
            content = row['content']
            w = int(row['w'])
            h = int(row['h'])
            x = int(row['x'])
            y = int(row['y'])
            ocr.append({
                'content': content,
                'w': w,
                'h': h,
                'x': x,
                'y': y,
            })
    else:
        if result is not None:
            # What comes back from fedora is 8-bit bytes
            for index, word in enumerate(result.decode('UTF-8-sig').strip().split('\r\n')):
                if len(word.split('\t')) == 5:
                    ocr.append({
                        'content': word.split('\t')[4],
                        'w': int(word.split('\t')[2]),
                        'h': int(word.split('\t')[3]),
                        'x': int(word.split('\t')[0]),
                        'y': int(word.split('\t')[1])
                    })
    if ocr:
        return ocr
    return None

def fetch_alto_ocr(canvas):
    """Function to fetch Alto OCR data for a given canvas.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :return: Positional OCR data
    :rtype: requests.models.Response
    """
    if 'archivelab' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        return None
    url = "{p}{c}/datastreams/tei/content".format(
        p=settings.DATASTREAM_PREFIX,
        c=canvas.pid.replace('fedora:', '')
    )
    return fetch_url(url, format='text/plain')

def add_alto_ocr(result):
    """Function to add fetched Alto OCR data for a given canvas.

    :param result: Fetched OCR data
    :type result: requests.models.Response
    :return: Parsed Alto OCR data
    :rtype: list
    """
    if result is None:
        return None
    ocr = []
    surface = ElementTree.fromstring(result)[-1][0]
    for zones in surface:
        if 'zone' in zones.tag:
            for line in zones:
                # if line[-1].text is None:
                #     continue
                ocr.append({
                    'content': line[-1].text,
                    'h': int(line.attrib['lry']) - int(line.attrib['uly']),
                    'w': int(line.attrib['lrx']) - int(line.attrib['ulx']),
                    'x': int(line.attrib['ulx']),
                    'y': int(line.attrib['uly'])
                })
    if ocr:
        return ocr
    return None
