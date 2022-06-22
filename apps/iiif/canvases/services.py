# pylint: disable=invalid-name
"""Module to provide some common functions for Canvas objects."""
import csv
import pysftp
from tempfile import gettempdir
from io import BytesIO
import json
from os import environ, path, unlink, remove
import re
import tempfile
from hocr_spec import HocrValidator
from lxml import etree
from django.conf import settings
from django.core.serializers import deserialize
import httpretty
from apps.iiif.annotations.models import Annotation
from apps.utils.fetch import fetch_url

class IncludeQuotesDialect(csv.Dialect): # pylint: disable=too-few-public-methods
    """Subclass of csv.Dialect to include the quote marks in OCR content."""
    # include the quote marks in content
    lineterminator = '\n'
    delimiter = '\t'
    quoting = csv.QUOTE_NONE # perform no special processing of quote characters

class HocrValidationError(Exception):
    """Exception for hOCR validation errors."""
    pass # pylint: disable=unnecessary-pass

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

    httpretty.register_uri(httpretty.GET, f'{canvas.resource_id}/info.json', body=iiif_image_info)

def get_ocr(canvas):
    """Function to determine method for fetching OCR for a canvas.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :return: List of dicts of parsed OCR data.
    :rtype: list
    """
    if canvas.default_ocr == "line":
        result = fetch_tei_ocr(canvas)
        return parse_tei_ocr(result)

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
        f'{canvas.resource_id}/info.json',
        timeout=settings.HTTP_REQUEST_TIMEOUT,
        data_format='json'
    )

    return response

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

    url = "{p}{c}{s}".format(
        p=settings.DATASTREAM_PREFIX,
        c=canvas.pid.replace('fedora:', ''),
        s=settings.DATASTREAM_SUFFIX
    )

    if (
        environ['DJANGO_ENV'] == 'test'
        and 'images.readux.ecds.emory' not in canvas.manifest.image_server.server_base
        and canvas.ocr_file_path is None
    ):
        fake_json = open(path.join(settings.APPS_DIR, 'iiif/canvases/fixtures/ocr_words.json'))
        words = fake_json.read()
        httpretty.enable(allow_net_connect=True)
        httpretty.register_uri(httpretty.GET, url, body=words)

    if canvas.ocr_file_path is not None:
        if canvas.image_server.storage_service == 's3':
            return canvas.image_server.bucket.Object(canvas.ocr_file_path).get()['Body'].read()
        if canvas.image_server.storage_service == 'sftp':
            try:
                httpretty.enable(allow_net_connect=True)
                connection_options = pysftp.CnOpts()
                connection_options.hostkeys = None
                sftp = pysftp.Connection(**canvas.image_server.sftp_connection, cnopts=connection_options)
                ocr_local_file_path = path.join(gettempdir(), canvas.ocr_file_path)
                sftp.get(canvas.ocr_file_path, localpath=ocr_local_file_path)

                with open(ocr_local_file_path, 'r') as ocr_file:
                    ocr_contents = ocr_file.read()

                remove(ocr_local_file_path)

                return ocr_contents.encode()
            except:
                return None

    return fetch_url(url, data_format='text/plain')

def is_json(to_test):
    """Function to test if data is shaped like JSON.

    :param to_test: String or bytes
    :type to_test: requests.models.Response
    :return: True if shaped like JSON, False if not.
    :rtype: bool
    """
    if isinstance(to_test, bytes):
        as_str = to_test.decode('utf-8')
    else:
        as_str = str(to_test)
    try:
        json.loads(as_str)
    except ValueError:
        return False
    return True

def is_tsv(to_test):
    """Function to test if data is shaped like a TSV.

    :param to_test: String or bytes
    :type to_test: requests.models.Response
    :return: True if shaped like a TSV, False if not.
    :rtype: bool
    """
    if isinstance(to_test, bytes):
        as_str = to_test.decode('utf-8')
        as_list = as_str.splitlines()
    else:
        as_str = str(to_test)
        as_list = as_str.split('\n')
    if len(as_list) > 1:
        if len(as_str.split('\t')) > 1:
            return True
    return False

def add_positional_ocr(canvas, result):
    """Function to disambiguate and parse fetched OCR data for a canvas.

    :param canvas: Canvas object
    :type canvas: apps.iiif.canvases.models.Canvas
    :param result: Previously fetched OCR data
    :type result: requests.models.Response
    :return: List of dicts of parsed OCR data.
    :rtype: list
    """
    if result is None:
        return None
    if canvas.ocr_file_path is None:
        if isinstance(result, dict) or is_json(result):
            ocr = parse_dict_ocr(result)
        elif is_tsv(result) and isinstance(result, bytes):
            if result.decode('utf-8') == result.decode('UTF-8-sig'):
                ocr = parse_tsv_ocr(result)
            else:
                ocr = parse_fedora_ocr(result)
        elif is_tsv(result):
            ocr = parse_tsv_ocr(result)
    elif canvas.ocr_file_path.endswith('.json'):
        ocr = parse_dict_ocr(result)
    elif canvas.ocr_file_path.endswith('.tsv') or canvas.ocr_file_path.endswith('.tab'):
        ocr = parse_tsv_ocr(result)
    elif canvas.ocr_file_path.endswith('.xml'):
        ocr = parse_xml_ocr(result)
    elif canvas.ocr_file_path.endswith('.hocr'):
        ocr = parse_hocr_ocr(result)
    if ocr:
        return ocr
    return None

def parse_alto_ocr(result):
    """Function to parse fetched ALTO OCR data for a given canvas.

    :param result: Fetched ALTO OCR data
    :type result: requests.models.Response
    :return: Parsed OCR data
    :rtype: list
    """
    if result is None:
        return None
    ocr = []
    unvalidated_root = etree.fromstring(result)
    if 'ns-v2' in unvalidated_root.tag:
        schema_file = 'xml_schema/alto-2-1.xsd'
    elif 'ns-v3' in unvalidated_root.tag:
        schema_file = 'xml_schema/alto-3-1.xsd'
    elif 'ns-v4' in unvalidated_root.tag:
        schema_file = 'xml_schema/alto-4-2.xsd'
    else:
        schema_file = 'xml_schema/alto-1-4.xsd'
    parser = etree.XMLParser(schema = etree.XMLSchema(file=schema_file))
    # The following will raise etree.XMLSyntaxError if invalid
    root = etree.fromstring(result, parser=parser)
    strings = root.findall('.//String')
    if not strings:
        strings = root.findall('.//{*}String')
    for string in strings:
        attrib =  {k.lower(): v for k, v in string.attrib.items()}
        ocr.append({
            'content': attrib['content'],
            'h': int(attrib['height']),
            'w': int(attrib['width']),
            'x': int(attrib['hpos']),
            'y': int(attrib['vpos'])
        })
    if ocr:
        return ocr
    return None

def parse_hocr_ocr(result):
    """Function to parse fetched hOCR data for a given canvas.

    :param result: Fetched hOCR data
    :type result: requests.models.Response
    :return: Parsed OCR data
    :rtype: list
    """
    if isinstance(result, bytes):
        as_string = result.decode('utf-8')
    else:
        as_string = str(result)
    # Regex to ignore x_size, x_ascenders, x_descenders. this is a known issue with
    # tesseract producded hOCR: https://github.com/tesseract-ocr/tesseract/issues/3303
    result_without_invalid = re.sub(
        r'([ ;]+)(x_size [0-9\.\-;]+)|( x_descenders [0-9\.\-;]+)|( x_ascenders [0-9\.\-;]+)',
        repl='', string=as_string
    )
    file_like_hocr = BytesIO(result_without_invalid.encode('utf-8'))
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        file_like_hocr.seek(0)
        tmp_file.write(file_like_hocr.read())
        tmp_file.flush()
        temp_file_name = tmp_file.name
    validator = HocrValidator(profile='relaxed')
    report = validator.validate(source=temp_file_name)
    is_valid = report.format('bool')
    if not is_valid:
        report_text = report.format('text')
        unlink(temp_file_name)
        raise HocrValidationError(str(report_text))
    unlink(temp_file_name)
    ocr = []
    file_like_hocr.seek(0)
    tree = etree.parse(file_like_hocr)
    words = tree.findall(".//span[@class]")
    if not words:
        words = tree.findall(".//{*}span[@class]")
    for word in words:
        if word.attrib['class'] == 'ocrx_word':
            all_attribs = word.attrib['title'].split(';')
            bbox = next((attrib for attrib in all_attribs if 'bbox' in attrib), '')
            # Splitting 'bbox x0 y0 x1 y1'
            bbox_attribs = bbox.split(' ')
            if len(bbox_attribs) == 5:
                ocr.append({
                    'content': word.text,
                    'h': int(bbox_attribs[4]) - int(bbox_attribs[2]),
                    'w': int(bbox_attribs[3]) - int(bbox_attribs[1]),
                    'x': int(bbox_attribs[1]),
                    'y': int(bbox_attribs[2])
                })
    if ocr:
        return ocr
    return None

def parse_dict_ocr(result):
    """Function to parse dict or JSON OCR data.

    :param result: Fetched dict OCR data
    :type result: requests.models.Response
    :return: Parsed OCR data
    :rtype: list
    """
    ocr = []
    if isinstance(result, bytes):
        as_string = result.decode('utf-8')
        as_dict = json.loads(as_string)
    elif isinstance(result, str):
        as_dict = json.loads(result)
    else:
        as_dict = result
    if 'ocr' in as_dict and as_dict['ocr'] is not None:
        for index, word in enumerate(as_dict['ocr']):  # pylint: disable=unused-variable
            if len(word) > 0:
                for w in word:
                    ocr.append({
                        'content': w[0],
                        'w': (w[1][2] - w[1][0]),
                        'h': (w[1][1] - w[1][3]),
                        'x': w[1][0],
                        'y': w[1][3],
                    })
    if ocr:
        return ocr
    return None

def parse_tei_ocr(result):
    """Function to parse fetched TEI OCR data for a given canvas.

    :param result: Fetched TEI OCR data
    :type result: requests.models.Response
    :return: Parsed OCR data
    :rtype: list
    """
    if result is None:
        return None
    ocr = []
    parser = etree.XMLParser(schema = etree.XMLSchema(file='xml_schema/tei_all.xsd'))
    # The following will raise etree.XMLSyntaxError if invalid
    surface = etree.fromstring(result, parser=parser)[-1][0]
    for zones in surface:
        if 'zone' in zones.tag:
            for line in zones:
                # if line[-1].text is None:
                #     continue
                ocr.append({
                    'content': line[-1].text,
                    'h': int(line.get('lry')) - int(line.get('uly')),
                    'w': int(line.get('lrx')) - int(line.get('ulx')),
                    'x': int(line.get('ulx')),
                    'y': int(line.get('uly'))
                })
    if ocr:
        return ocr
    return None

def parse_tsv_ocr(result):
    """Function to parse fetched TSV OCR data for a given canvas.

    :param result: Fetched TSV OCR data
    :type result: requests.models.Response
    :return: Parsed OCR data
    :rtype: list
    """
    ocr = []
    if isinstance(result, bytes):
        lines = result.decode('utf-8').splitlines()
    else:
        lines = str(result).split('\n')

    # Sometimes the TSV has some extra tabs at the beginning and the end. These have
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
    if ocr:
        return ocr
    return None

def parse_fedora_ocr(result):
    """Function to parse fetched Fedora OCR data for a given canvas.

    :param result: Fetched Fedora OCR data (bytes)
    :type result: requests.models.Response
    :return: Parsed OCR data
    :rtype: list
    """
    ocr = []
    if isinstance(result, bytes):
        # What comes back from fedora is 8-bit bytes
        for _, word in enumerate(result.decode('UTF-8-sig').strip().split('\r\n')):
            if len(word.split('\t')) == 5:
                ocr.append({
                    'content': word.split('\t')[4],
                    'w': int(word.split('\t')[2]),
                    'h': int(word.split('\t')[3]),
                    'x': int(word.split('\t')[0]),
                    'y': int(word.split('\t')[1])
                })
    return ocr

def parse_xml_ocr(result):
    """Function to determine the flavor of XML OCR and then parse accordingly.

    :param result: Fetched XML OCR data
    :type result: requests.models.Response
    :return: Parsed OCR data
    :rtype: list
    """
    root = etree.fromstring(result)
    if (
        re.match(r'{[0-9A-Za-z.:/#-]+}alto|alto', root.tag)
        or 'www.loc.gov/standards/alto' in root.find('.//*').tag
    ):
        return parse_alto_ocr(result)
    if root.find('.//teiHeader') is not None or root.find('.//{*}teiHeader') is not None:
        return parse_tei_ocr(result)
    if root.find('.//div') is not None or root.find('.//{*}div') is not None:
        # Fallback to hOCR if it looks like XHTML
        return parse_hocr_ocr(result)
    return None

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

def add_oa_annotations(annotation_list_url):
    data = fetch_url(annotation_list_url)
    for oa_annotation in data['resources']:
        anno = deserialize('annotation', oa_annotation)
        anno.save()