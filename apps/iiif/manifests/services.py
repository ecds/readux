""" Module of service classes and methods for ingest. """

import itertools
import re
from mimetypes import guess_type
from urllib.parse import unquote, urlparse

from django.apps import apps
from tablib.core import Dataset

from .models import Manifest, RelatedLink


def clean_metadata(metadata):
    """Normalize names of fields that align with Manifest fields.

    :param metadata:
    :type metadata: tablib.Dataset
    :return: Dictionary with keys matching Manifest fields
    :rtype: dict
    """
    fields = [f.name for f in Manifest._meta.get_fields()]
    metadata = {
        (
            key.casefold().replace(" ", "_")
            if key.casefold().replace(" ", "_") in fields
            else key
        ): value
        for key, value in metadata.items()
    }

    for key in metadata.keys():
        if key != "metadata" and isinstance(metadata[key], list):
            if isinstance(metadata[key][0], dict):
                for meta_key in metadata[key][0].keys():
                    if "value" in meta_key:
                        metadata[key] = metadata[key][0][meta_key]
            else:
                metadata[key] = ", ".join(metadata[key])

    return metadata


def create_related_links(manifest, related_str):
    """
    Create RelatedLink objects from supplied related links string and associate each with supplied
    Manifest. String should consist of semicolon-separated URLs.
    :param manifest:
    :type manifest: iiif.manifest.models.Manifest
    :param related_str:
    :type related_str: str
    :rtype: None
    """
    for link in related_str.split(";"):
        (format, _) = guess_type(link)
        RelatedLink.objects.create(
            manifest=manifest,
            link=link,
            format=format
            or "text/html",  # assume web page if MIME type cannot be determined
            is_structured_data=False,  # assume this is not meant for seeAlso
        )


def set_metadata(manifest, metadata):
    """
    Update Manifest.metadata using supplied metadata dict
    :param manifest:
    :type manifest: iiif.manifest.models.Manifest
    :param metadata:
    :type metadata: dict
    :rtype: None
    """
    fields = [f.name for f in Manifest._meta.get_fields()]
    for key, value in metadata.items():
        casefolded_key = key.casefold().replace(" ", "_")
        if casefolded_key == "related":
            # add RelatedLinks from metadata spreadsheet key "related"
            create_related_links(manifest, value)
        elif casefolded_key in fields:
            setattr(manifest, casefolded_key, value)
        else:
            # all other keys go into Manifest.metadata JSONField
            if isinstance(manifest.metadata, list):
                found_index = next(
                    (
                        idx
                        for (idx, d) in enumerate(manifest.metadata)
                        if "label" in d and d["label"] == key
                    ),
                    None,
                )
                if found_index:
                    # if value with this label exists, pop and re-insert
                    manifest.metadata.pop(found_index)
                    manifest.metadata.insert(
                        found_index, {"label": key, "value": value}
                    )
                else:
                    # if not, add label and value to end of list
                    manifest.metadata.append({"label": key, "value": value})
            elif isinstance(manifest.metadata, dict):
                # convert to list of {label, value} as expected by iiif spec
                manifest.metadata = [
                    *[{"label": k, "value": v} for (k, v) in manifest.metadata.items()],
                    {"label": key, "value": value},
                ]
            else:
                # instantiate as list
                manifest.metadata = [{"label": key, "value": value}]
    manifest.save()


def create_manifest(ingest):
    """
    Create or update a Manifest from supplied metadata and images.
    :return: New or updated Manifest with supplied `pid`
    :rtype: iiif.manifest.models.Manifest
    """
    manifest = None
    # Make a copy of the metadata so we don't extract it over and over.
    try:
        if not bool(ingest.manifest) or ingest.manifest is None:
            ingest.open_metadata()

        metadata = dict(ingest.metadata)
    except TypeError:
        metadata = None
    if metadata:
        if "pid" in metadata:
            manifest, created = Manifest.objects.get_or_create(
                pid=metadata["pid"].replace("_", "-")
            )
        else:
            manifest = Manifest.objects.create()
        set_metadata(manifest, metadata)
    else:
        manifest = Manifest()

    manifest.image_server = ingest.image_server

    # This was giving me a 'django.core.exceptions.AppRegistryNotReady: Models aren't loaded yet' error.
    Remote = apps.get_model("ingest.remote")

    # Ensure that manifest has an ID before updating the M2M relationship
    manifest.save()
    if not isinstance(ingest, Remote):
        manifest.refresh_from_db()
        manifest.collections.set(ingest.collections.all())
        # Save again once relationship is set
        manifest.save()
    else:
        RelatedLink(
            manifest=manifest,
            link=ingest.remote_url,
            format="application/ld+json",
            is_structured_data=True,
        ).save()

    return manifest


def extract_image_server(canvas):
    """Determines the IIIF image server URL for a given IIIF Canvas

    :param canvas: IIIF Canvas
    :type canvas: dict
    :return: IIIF image server URL
    :rtype: str
    """
    url = urlparse(canvas["images"][0]["resource"]["service"]["@id"])
    parts = url.path.split("/")
    parts.pop()
    base_path = "/".join(parts)
    host = url.hostname
    if url.port is not None:
        host = "{h}:{p}".format(h=url.hostname, p=url.port)
    return "{s}://{h}{p}".format(s=url.scheme, h=host, p=base_path)


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

    if "metadata" in data:
        manifest_data.append({"metadata": data["metadata"]})

        for iiif_metadata in [
            {prop["label"]: prop["value"]} for prop in data["metadata"]
        ]:
            properties.update(iiif_metadata)

    # Sometimes, the label appears as a list.
    if "label" in data.keys() and isinstance(data["label"], list):
        data["label"] = " ".join(data["label"])

    manifest_data.extend(
        [{prop: data[prop]} for prop in data if isinstance(data[prop], str)]
    )

    for datum in manifest_data:
        properties.update(datum)

    uri = urlparse(data["@id"])

    if not uri.query:
        properties["pid"] = uri.path.split("/")[-2]
    else:
        properties["pid"] = uri.query

    if "description" in data.keys():
        if isinstance(data["description"], list):
            if isinstance(data["description"][0], dict):
                en = [
                    lang["@value"]
                    for lang in data["description"]
                    if lang["@language"] == "en"
                ]
                properties["summary"] = (
                    data["description"][0]["@value"] if not en else en[0]
                )
            else:
                properties["summary"] = data["description"][0]
        else:
            properties["summary"] = data["description"]

    if "logo" in properties:
        properties["logo_url"] = properties["logo"]
        properties.pop("logo")

    manifest_metadata = clean_metadata(properties)

    return manifest_metadata


def parse_iiif_v2_canvas(canvas):
    """ """
    canvas_id = canvas["@id"].split("/")
    pid = canvas_id[-1] if canvas_id[-1] != "canvas" else canvas_id[-2]

    service = urlparse(canvas["images"][0]["resource"]["service"]["@id"])
    resource = unquote(service.path.split("/").pop())

    summary = canvas["description"] if "description" in canvas.keys() else ""
    label = canvas["label"] if "label" in canvas.keys() else ""
    return {
        "pid": pid,
        "height": canvas["height"],
        "width": canvas["width"],
        "summary": summary,
        "label": label,
        "resource": resource,
    }


def get_metadata_from(files):
    """
    Find metadata file in uploaded files.
    :return: If metadata file exists, returns the values. If no file, returns None.
    :rtype: list or None
    """
    metadata = None
    for file in files:
        if metadata is not None:
            continue
        if "zip" in guess_type(file.name)[0]:
            continue
        if "metadata" in file.name.casefold():
            stream = file.read()
            if (
                "csv" in guess_type(file.name)[0]
                or "tab-separated" in guess_type(file.name)[0]
            ):
                metadata = Dataset().load(stream.decode("utf-8-sig"), format="csv").dict
            else:
                metadata = Dataset().load(stream).dict
    return metadata


def get_associated_meta(all_metadata, file):
    """
    Associate metadata with filename.
    :return: If a matching filename is found, returns the row as dict,
        with generated pid. Otherwise, returns {}.
    :rtype: dict
    """
    file_meta = {}
    extless_filename = file.name[0 : file.name.rindex(".")]
    for meta_dict in all_metadata:
        metadata_found_filename = None
        for key, val in meta_dict.items():
            if key.casefold() == "filename":
                metadata_found_filename = val
        # Match filename column, case-sensitive, against filename
        if metadata_found_filename and metadata_found_filename in (
            extless_filename,
            file.name,
        ):
            file_meta = meta_dict
    return file_meta


def normalize_header(iterator):
    """Normalize the header row of a metadata CSV"""
    # ignore unicode characters and strip whitespace
    header_row = next(iterator).encode("ascii", "ignore").decode().strip()
    # lowercase the word "pid" in this row so we can access it easily
    header_row = re.sub(r"[Pp][Ii][Dd]", lambda m: m.group(0).casefold(), header_row)
    return itertools.chain([header_row], iterator)
