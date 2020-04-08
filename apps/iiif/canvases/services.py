import requests
import json
import csv
from django.conf import settings
from apps.utils.fetch import fetch_url
import config.settings.local as local_settings
from xml.etree import ElementTree
import httpretty

# Method to mock a response for testing.
@httpretty.activate
def get_fake_canvas_info(canvas):
    iiif_image_info = '{"@context": "http://iiif.io/api/image/2/context.json", "@id": "https://images.readux.ecds.emory.edu:8443/cantaloupe/iiif/2/osh-formal-mir_OSH-cover1.jpg", "protocol": "http://iiif.io/api/image", "width": 3000, "height": 3000, "sizes": [{"width": 122, "height": 106}, {"width": 245, "height": 212}, {"width": 490, "height": 423}, {"width": 979, "height": 847}, {"width": 1958, "height": 1694}, {"width": 3916, "height": 3387}], "tiles": [{"width": 979, "height": 847, "scaleFactors": [1, 2, 4, 8, 16, 32]}], "profile": ["http://iiif.io/api/image/2/level2.json", {"formats": ["jpg", "tif", "gif", "png"], "maxArea": 400000000, "qualities": ["bitonal", "default", "gray", "color"], "supports": ["regionByPx", "sizeByW", "sizeByWhListed", "cors", "regionSquare", "sizeByDistortedWh", "sizeAboveFull", "canonicalLinkHeader", "sizeByConfinedWh", "sizeByPct", "jsonldMediaType", "regionByPct", "rotationArbitrary", "sizeByH", "baseUriRedirect", "rotationBy90s", "profileLinkHeader", "sizeByForcedWh", "sizeByWh", "mirroring"]}]}'
    httpretty.register_uri(httpretty.GET, canvas.service_id, body=iiif_image_info)
    response = fetch_url(canvas.service_id, timeout=settings.HTTP_REQUEST_TIMEOUT, format='json')
    return response

def get_ocr(canvas):
    if canvas.default_ocr == "line":
        result = fetch_alto_ocr(canvas)
        return add_alto_ocr(canvas, result)
    elif canvas.default_ocr == "word" or canvas.default_ocr == "both":
        result = fetch_positional_ocr(canvas)
        return add_positional_ocr(canvas, result)

def get_canvas_info(canvas):
    """ Given a url, this function returns a dictionary of all collections."""
    if 'fake.info' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        return get_fake_canvas_info(canvas)

    return fetch_url(canvas.service_id, timeout=settings.HTTP_REQUEST_TIMEOUT, format='json')

# TODO figure out a way to test the fetch
def fetch_positional_ocr(canvas):
    if 'archivelab' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        return fetch_url("https://api.archivelab.org/books/{m}/pages/{p}/ocr?mode=words".format(m=canvas.manifest.pid, p=canvas.pid.split('$')[-1]))
    elif 'images.readux.ecds.emory' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        return fetch_url("https://raw.githubusercontent.com/ecds/ocr-bucket/master/{m}/{p}.tsv".format(m=canvas.manifest.pid, p=canvas.pid.split('_')[-1].replace('.jp2', '').replace('.jpg', '').replace('.tif', '')), format='text')
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
    elif 'images.readux.ecds.emory' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
            # include the quote marks in content
            class include_quotes_dialect(csv.Dialect):
                lineterminator = '\n'
                delimiter= '\t'
                quoting = csv.QUOTE_NONE # perform no special processing of quote characters
            reader = csv.DictReader(result.split('\n'), dialect=include_quotes_dialect)
            for row in reader:
                content = row['content']
                # # Skip empty strings
                # if content.isspace() or not content:
                #     continue
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

def fetch_alto_ocr(canvas):
    if 'archivelab' in canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE:
        return None
    else:
        url = "{p}{c}/datastreams/tei/content".format(p=settings.DATASTREAM_PREFIX, c=canvas.pid.replace('fedora:',''))
        return fetch_url(url, format='text/plain')

def add_alto_ocr(canvas, result):
    if result == None:
        return None
    ocr = []
    surface = ElementTree.fromstring(result)[-1][0]
    for zones in surface:
        if 'zone' in zones.tag:
            for line in zones:
                if line[-1].text is None:
                    continue
                ocr.append({
                    'content': line[-1].text,
                    'h': int(line.attrib['lry']) - int(line.attrib['uly']),
                    'w': int(line.attrib['lrx']) - int(line.attrib['ulx']),
                    'x': int(line.attrib['ulx']),
                    'y': int(line.attrib['uly'])
                })
    if (ocr):
        return ocr
    else:
        return None
