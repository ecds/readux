"""Elasticsearch indexing rules for IIIF manifests"""

from html import unescape

from django.conf import settings
from django.db.models.query import Prefetch
from django.utils.html import strip_tags

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from edtf import parse_edtf
from edtf.convert import struct_time_to_jd
from edtf.natlang import text_to_edtf
from elasticsearch_dsl import MetaField, Keyword, analyzer
from unidecode import unidecode

from apps.iiif.annotations.models import Annotation
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.models import Manifest

# TODO: Better English stemming (e.g. Rome to match Roman), multilingual stemming.
stemmer = analyzer(
    "en",
    tokenizer="standard",
    filter=["lowercase", "stop", "porter_stem"],
)


def _published_date_fallback_jd(instance, bound):
    """date_earliest/date_latest are derived from published_date_edtf, a
    separate field cataloguers are expected to fill in alongside the
    display-only published_date. In practice a lot of records only ever get
    published_date set, which silently excludes them from date-published
    filtering/sorting and miscounts them as "no date" even though they show
    a real date on screen. Fall back to parsing published_date itself so the
    search filter reflects what's actually displayed.
    """
    if not instance.published_date:
        return None
    try:
        edtf_string = text_to_edtf(instance.published_date)
        if not edtf_string:
            return None
        edtf_obj = parse_edtf(edtf_string, fail_silently=True)
        if not edtf_obj:
            return None
        struct_time = edtf_obj.lower_fuzzy() if bound == "lower" else edtf_obj.upper_fuzzy()
        return struct_time_to_jd(struct_time)
    except Exception:  # pylint: disable=broad-except
        # published_date is free-text catalog data; malformed/unparseable
        # values should degrade to "no fallback date", not break indexing.
        return None


@registry.register_document
class ManifestDocument(Document):
    """Elasticsearch Document class for IIIF Manifest"""

    # fields to map explicitly in Elasticsearch
    attribution = fields.TextField()
    authors = fields.KeywordField(multi=True)  # only used for faceting/filtering
    author = fields.TextField()  # only used for searching
    canvas_set = fields.NestedField(
        properties={
            "result": fields.TextField(analyzer=stemmer),
            "position": fields.IntegerField(),
            "pid": fields.KeywordField(),
        }
    )  # canvas_set.result = OCR annotation text on each canvas
    collections = fields.NestedField(properties={"label": fields.KeywordField()})
    date_earliest = fields.FloatField()
    date_latest = fields.FloatField()
    has_pdf = fields.BooleanField()
    label = fields.TextField(analyzer=stemmer)
    label_alphabetical = fields.KeywordField()
    languages = fields.KeywordField(multi=True)
    license = fields.TextField()
    metadata = fields.NestedField()
    pid = fields.KeywordField()
    published_city = fields.TextField()
    publisher = fields.TextField()
    summary = fields.TextField(analyzer=stemmer)

    class Index:
        """Settings for Elasticsearch"""

        name = f"{settings.INDEX_PREFIX}_manifests" if settings.INDEX_PREFIX else "manifests"
        settings = {
            "analysis": {
                "analyzer": {
                    "en": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "stop", "porter_stem"],
                    }
                }
            }
        }

    class Django:
        """Settings for automatically pulling data from Django"""

        model = Manifest
        ignore_signals = True
        # Django 4.2+ requires chunk_size when calling iterator() on a queryset
        # that uses prefetch_related(). This value is passed through as chunk_size.
        queryset_pagination = 2000

        # fields to map dynamically in Elasticsearch
        fields = [
            "created_at",
            "date_sort_ascending",
            "date_sort_descending",
            "published_date",
            "viewingdirection",
        ]
        related_models = [Canvas]

    class Meta:
        # make Keyword type default for strings, for custom dynamically-mapped facet fields
        dynamic_templates = MetaField(
            [
                {
                    "strings": {
                        "match_mapping_type": "string",
                        "mapping": Keyword().to_dict(),
                    }
                }
            ]
        )

    def should_index_object(self, obj):
        """
        Overwriting parent method.
        Only index volumes marked 'searchable'
        """
        return obj.searchable

    # def get_queryset(self):
    #     """
    #     Overwrite parent method to only include searchable volumes.
    #     """
    #     return self.django.model._default_manager.filter(searchable=True)

    def prepare_authors(self, instance):
        """convert authors string into list"""
        if instance.author:
            return [s.strip() for s in instance.author.split(";")]
        return ["[no author]"]

    def prepare_has_pdf(self, instance):
        """convert pdf field into boolean"""
        return bool(instance.pdf)

    def prepare_date_earliest(self, instance):
        """Fall back to parsing the display-only published_date when
        date_earliest is unset (see _published_date_fallback_jd)"""
        if instance.date_earliest is not None:
            return instance.date_earliest
        return _published_date_fallback_jd(instance, "lower")

    def prepare_date_latest(self, instance):
        """Fall back to parsing the display-only published_date when
        date_latest is unset (see _published_date_fallback_jd)"""
        if instance.date_latest is not None:
            return instance.date_latest
        return _published_date_fallback_jd(instance, "upper")

    def prepare_label_alphabetical(self, instance):
        """get the first 64 chars of a label, just for sorting purposes"""
        if instance.label:
            # use unidecode to unaccent characters
            return unidecode(instance.label[0:64], "utf-8")
        return "[no label]"

    def prepare_languages(self, instance):
        """convert languages into list of strings"""
        if instance.languages.count():
            return [lang.name for lang in instance.languages.all()]
        return ["[no language]"]

    def prepare_metadata(self, instance):
        """use custom metadata settings to prepare metadata field"""
        custom_metadata = {}

        if (
            settings
            and hasattr(settings, "CUSTOM_METADATA")
            and isinstance(settings.CUSTOM_METADATA, dict)
        ):
            # should be a dict like {meta_key: {"multi": bool, "separator": str}}
            for key, opts in filter(
                lambda item: item[1].get(
                    "faceted", False
                ),  # filter to only faceted fields
                settings.CUSTOM_METADATA.items(),
            ):
                val = None
                # each key in CUSTOM_METADATA dict should be a metadata key.
                # however, instance.metadata will generally be a list rather than a dict: it's a
                # jsonfield that maps to the IIIF manifest metadata field, which is a list
                # consisting of dicts like { label: str, value: str }
                if isinstance(instance.metadata, list):
                    # find matching value by "label" == key
                    for obj in instance.metadata:
                        if "label" in obj and obj["label"] == key and "value" in obj:
                            val = obj["value"]
                            break
                elif isinstance(instance.metadata, dict):
                    # in some cases it may be just a dict, so in that case, use get()
                    val = instance.metadata.get(key, None)
                # should have "multi" bool and if multi is True, "separator" string
                if val and opts.get("multi", False) == True:
                    val = val.split(opts.get("separator", ";"))
                custom_metadata[key] = val

        return custom_metadata

    def prepare_summary(self, instance):
        """Strip HTML tags from summary"""
        return unescape(strip_tags(instance.summary))

    def get_queryset(self):
        """prefetch related to improve performance"""
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "collections",
                "image_server",
                "languages",
                Prefetch(
                    "canvas_set",
                    queryset=Canvas.objects.prefetch_related(
                        Prefetch(
                            "annotation_set",
                            queryset=Annotation.objects.select_related("owner"),
                        ),
                    ),
                ),
            )
        )

    def get_instances_from_related(self, related_instance):
        """Retrieving item to index from related objects"""
        if isinstance(related_instance, Canvas):
            # many to many relationship
            return related_instance.manifest
