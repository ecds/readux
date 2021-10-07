# pylint: disable=invalid-name
"""Module to provide some common functions for Canvas objects."""
import csv
from os import environ, path
from django.core.exceptions import ValidationError
import pytest
from xml.etree import ElementTree
import httpretty
from django.conf import settings
from apps.iiif.annotations.models import Annotation
from apps.utils.fetch import fetch_url

class IncludeQuotesDialect(csv.Dialect): # pylint: disable=too-few-public-methods
    """Subclass of csv.Dialect to include the quote marks in OCR content."""
    # include the quote marks in content
    lineterminator = '\n'
    delimiter = '\t'
    quoting = csv.QUOTE_NONE # perform no special processing of quote characters

# @httpretty.activate
def activate_fake_canvas_info(canvas):
    """Function to mock a response for testing.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :return: OCR data
    :rtype: requests.models.Response
    """
    with open('apps/iiif/canvases/fixtures/info.json', 'r') as file:
        iiif_image_info = file.read().replace('\n', '')
    httpretty.register_uri(httpretty.GET, canvas.service_id, body=iiif_image_info)

def get_ocr(canvas):
    """Function to determine method for fetching OCR for a canvas.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :return: List of dicts of parsed OCR data.
    :rtype: list
    """
    if canvas.default_ocr == "line":
        result = fetch_tei_ocr(canvas)
        return add_tei_ocr(result)

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
    if environ['DJANGO_ENV'] == 'test':
        httpretty.enable(allow_net_connect=False)
        activate_fake_canvas_info(canvas)
        # return response

    response = fetch_url(
        canvas.resource_id,
        timeout=settings.HTTP_REQUEST_TIMEOUT,
        data_format='json'
    )
    return response


# TODO: Maybe add "OCR Source" and "OCR Type" attributes to the manifest model. That might
# help make this more universal.
def fetch_positional_ocr(canvas):
    """Function to get OCR for a canvas depending on the image's source.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :return: Positional OCR data
    :rtype: requests.models.Response
    """
    if 'archivelab' in canvas.manifest.image_server.server_base:
        if '$' in canvas.pid:
            pid = str(int(canvas.pid.split('$')[-1]) - canvas.ocr_offset)
        else:
            pid = canvas.pid

        url = f"https://api.archivelab.org/books/{canvas.manifest.pid}/pages/{pid}/ocr?mode=words"

        if environ['DJANGO_ENV'] == 'test':
            fake_ocr = open(path.join(settings.APPS_DIR, 'iiif/canvases/fixtures/ocr_words.json'))
            words = fake_ocr.read()
            httpretty.enable()
            httpretty.register_uri(httpretty.GET, url, body=words)

        return fetch_url(url)

    if 'images.readux.ecds.emory' in canvas.manifest.image_server.server_base:
        # Fake TSV data for testing.
        if environ['DJANGO_ENV'] == 'test':
            fake_tsv = open(path.join(settings.APPS_DIR, 'iiif/canvases/fixtures/sample.tsv'))
            tsv = fake_tsv.read()
            url = "https://raw.githubusercontent.com/ecds/ocr-bucket/master/{m}/boo.tsv".format(
                m=canvas.manifest.pid
            )
            httpretty.enable()
            httpretty.register_uri(httpretty.GET, url, body=tsv)

        if canvas.ocr_file_path is None:
            return fetch_url(
                "https://raw.githubusercontent.com/ecds/ocr-bucket/master/{m}/{p}.tsv".format(
                    m=canvas.manifest.pid,
                    p=canvas.pid.split('_')[-1]
                    .replace('.jp2', '')
                    .replace('.jpg', '')
                    .replace('.tif', '')
                ),
                data_format='text'
            )

        if canvas.image_server.storage_service == 's3':
            return canvas.image_server.bucket.Object(canvas.ocr_file_path).get()['Body'].read()

            # return fetch_url(canvas.ocr_file_path, data_format='text')
        # Not sure we will need this. Leaving just as a reminder.
        # else:
        #     file = open(canvas.ocr_file_path)
        #     data = file.read()
        #     file.close()
        #     return data

    url = "{p}{c}{s}".format(
        p=settings.DATASTREAM_PREFIX,
        c=canvas.pid.replace('fedora:', ''),
        s=settings.DATASTREAM_SUFFIX
    )

    if environ['DJANGO_ENV'] == 'test':
        fake_tei = open(path.join(settings.APPS_DIR, 'iiif/canvases/fixtures/ocr_words.json'))
        words = fake_tei.read()
        httpretty.enable()
        httpretty.register_uri(httpretty.GET, url, body=words)


    return fetch_url(url, data_format='text/plain')

def add_positional_ocr(canvas, result):
    """Function to parse fetched OCR data for a canvas.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :param result: Previously fetched OCR data
    :type result: requests.models.Response
    :return: List of dicts of parsed OCR data.
    :rtype: list
    """
    if result is None:
        return None
    ocr = []
    if 'archivelab' in canvas.manifest.image_server.server_base:
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
    elif 'images.readux.ecds.emory' in canvas.manifest.image_server.server_base:

        lines = str(result).split('\n')

        # Sometimes the TSV has some extra tabs at the beginign and the end. These have
        # to be cleaned out. It gets complicatied.
        for index, line in enumerate(lines):
            # First we remove any leading column that is empty.
            line = line.strip()
            lines[index] = line
            # It might be true that the "content" column is empty. However, we just
            # removed it. So we have to add it back.
            if lines[index].count('\t') == 3:
                lines[index] = ' \t' + lines[index]

        reader = csv.DictReader(lines, dialect=IncludeQuotesDialect)

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

def fetch_tei_ocr(canvas):
    """Function to fetch TEI OCR data for a given canvas.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :return: Positional OCR data
    :rtype: requests.models.Response
    """
    if 'archivelab' in canvas.manifest.image_server.server_base:
        return None
    url = "{p}{c}/datastreams/tei/content".format(
        p=settings.DATASTREAM_PREFIX,
        c=canvas.pid.replace('fedora:', '')
    )

    return fetch_url(url, data_format='text/plain')

def add_tei_ocr(result):
    """Function to add fetched TEI OCR data for a given canvas.

    :param result: Fetched OCR data
    :type result: requests.models.Response
    :return: Parsed TEI OCR data
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

def add_alto_ocr(result):
    """Function to add fetched ALTO OCR data for a given canvas.

    :param result: Fetched OCR data
    :type result: requests.models.Response
    :return: Parsed ALTO OCR data
    :rtype: list
    """
    if result is None:
        return None
    ocr = []
    root = ElementTree.fromstring(result)
    if not is_valid_alto(root):
        raise ValidationError
    strings = root.find('.//String')
    for string in strings:
        ocr.append({
            'content': string.get('content').text,
            'h': int(string.get('height')),
            'w': int(string.get('width')),
            'x': int(string.get('hpos')),
            'y': int(string.get('vpos'))
        })
    if ocr:
        return ocr
    return None

def is_valid_alto(xml_root):
    """Function to check validity of ALTO OCR data.

    :param xml_root: OCR data
    :type xml_root: xml.etree.ElementTree
    :return: True if valid, False if invalid
    :rtype: bool
    """
    if xml_root.tag != 'alto':
        return False
    return True

def add_ocr_annotations(canvas, ocr):
    word_order = 1
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
