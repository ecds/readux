""" Module of service classes and methods for ingest. """
from urllib.parse import unquote, urlparse
from uuid import uuid4
import boto3
from django.apps import apps
from apps.iiif.manifests.models import Manifest
from apps.iiif.manifests.models import Manifest, RelatedLink

def clean_metadata(metadata):
    """Remove keys that do not aligin with Manifest fields.

    :param metadata:
    :type metadata: tablib.Dataset
    :return: Dictionary with keys matching Manifest fields
    :rtype: dict
    """
    metadata = {k.casefold().replace(' ', '_'): v for k, v in metadata.items()}
    fields = [f.name for f in Manifest._meta.get_fields()]
    invalid_keys = []

    for key in metadata.keys():
        if key not in fields:
            invalid_keys.append(key)

    for invalid_key in invalid_keys:
        metadata.pop(invalid_key)

    return metadata

def create_manifest(ingest):
    """
    Create or update a Manifest from supplied metadata and images.
    :return: New or updated Manifest with supplied `pid`
    :rtype: iiif.manifest.models.Manifest
    """
    manifest = None
    # Make a copy of the metadata so we don't extract it over and over.
    metadata = ingest.metadata
    if metadata is not None:
        manifest, created = Manifest.objects.get_or_create(pid=metadata['pid'].replace('_', '-'))
        for (key, value) in metadata.items():
            setattr(manifest, key, value)
        if not created:
            manifest.canvas_set.all().delete()
    else:
        manifest = Manifest(pid=str(uuid4()))

    manifest.image_server = ingest.image_server
    manifest.save()

    # This was giving me a 'django.core.exceptions.AppRegistryNotReady: Models aren't loaded yet' error.
    # Remote = apps.get_model('ingest.remote')
    # if type(ingest, .models.Remote):
    if type(ingest) == 'apps.ingest.model.Local':
        RelatedLink(
            manifest=manifest,
            link=ingest.remote_url,
            format='application/ld+json'
        ).save()

    return manifest

def extract_image_server(canvas):
    """Determins the IIIF image server URL for a given IIIF Canvas

    :param canvas: IIIF Canvas
    :type canvas: dict
    :return: IIIF image server URL
    :rtype: str
    """
    url = urlparse(canvas['images'][0]['resource']['service']['@id'])
    parts = url.path.split('/')
    parts.pop()
    base_path = '/'.join(parts)
    host = url.hostname
    if url.port is not None:
        host = '{h}:{p}'.format(h=url.hostname, p=url.port)
    return '{s}://{h}{p}'.format(s=url.scheme, h=host, p=base_path)

def parse_iiif_v2_manifest(data):
    """Parse IIIF Manifest based on v2.1.1 or the presentation API.
    https://iiif.io/api/presentation/2.1

    :param data: IIIF Presentation v2.1.1 manifest
    :type data: dict
    :return: Extracted metadata
    :rtype: dict
    """
    properties = {}
    manifest_data = []

    if 'metadata' in data:
        manifest_data.append({ 'metadata': data['metadata'] })

        for iiif_metadata in [{prop['label']: prop['value']} for prop in data['metadata']]:
            properties.update(iiif_metadata)

    # Sometimes, that label appears as a list.
    if 'label' in data.keys() and isinstance(data['label'], list):
        data['label'] = ' '.join(data['label'])

    manifest_data.extend([{prop: data[prop]} for prop in data if isinstance(data[prop], str)])

    for datum in manifest_data:
        properties.update(datum)

    properties['pid'] = urlparse(data['@id']).path.split('/')[-2]
    properties['summary'] = data['description'] if 'description' in data else ''

    # TODO: Work out adding remote logos
    if 'logo' in properties:
        properties.pop('logo')

    manifest_metadata = clean_metadata(properties)

    return manifest_metadata

def parse_iiif_v2_canvas(canvas):
    """ """
    canvas_id = canvas['@id'].split('/')
    pid = canvas_id[-1] if canvas_id[-1] != 'canvas' else canvas_id[-2]

    service = urlparse(canvas['images'][0]['resource']['service']['@id'])
    resource = unquote(service.path.split('/').pop())

    summary = canvas['description'] if 'description' in canvas.keys() else ''
    label = canvas['label'] if 'label' in canvas.keys() else ''
    return {
        'pid': pid,
        'height': canvas['height'],
        'width': canvas['width'],
        'summary': summary,
        'label': label,
        'resource': resource
    }
