# pylint: disable=invalid-name
"""Module to provide some common functions for Canvas objects."""
import csv
from os import path
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
    response = fetch_url(
        canvas.resource_id,
        timeout=settings.HTTP_REQUEST_TIMEOUT,
        data_format='json'
    )
    return response

def get_fake_ocr():
    """Generate fake OCR data for testing.

    :return: OCR data
    :rtype: dict
    """
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
    if 'fake.info' in canvas.manifest.image_server.server_base:
        return get_fake_ocr()
    if canvas.default_ocr == "line":
        result = None
        if 'fake' in canvas.manifest.image_server.server_base:
            result = open('apps/iiif/canvases/fixtures/alto.xml', 'r').read()
        else:
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
    if 'fake' in str(canvas.manifest.image_server.server_base):
        response =  get_fake_canvas_info(canvas)
        return response

    response = fetch_url(canvas.resource_id, timeout=settings.HTTP_REQUEST_TIMEOUT, data_format='json')
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
        url = None

        if '$' in canvas.pid:
            pid = str(int(canvas.pid.split('$')[-1]) - canvas.ocr_offset)
        else:
            pid = canvas.pid

        url = f"https://api.archivelab.org/books/{canvas.manifest.pid}/pages/{pid}/ocr?mode=words"

        if 'fake' in canvas.manifest.image_server.server_base:
            fake_ocr = open(path.join(settings.APPS_DIR, 'iiif/canvases/fixtures/ocr_words.json'))
            ocr = fake_ocr.read()
            fake_ocr.close()
            httpretty.enable()
            httpretty.register_uri(
                httpretty.GET,
                url,
                body=ocr,
                content_type='text/json"'
            )

        return fetch_url(url)

    if 'images.readux.ecds.emory' in canvas.manifest.image_server.server_base:
        # Fake TSV data for testing.
        if 'fake' in canvas.manifest.image_server.server_base:
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

        file = open(canvas.ocr_file_path)
        data = file.read()
        file.close()
        return data

    return fetch_url(
        "{p}{c}{s}".format(
            p=settings.DATASTREAM_PREFIX,
            c=canvas.pid.replace('fedora:', ''),
            s=settings.DATASTREAM_SUFFIX), data_format='text/plain'
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

        lines = result.split('\n')
        # if (lines[0].startswith(content)):
        #     lines.pop(0)
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

def fetch_alto_ocr(canvas):
    """Function to fetch Alto OCR data for a given canvas.

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
