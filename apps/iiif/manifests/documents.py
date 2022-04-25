"""Elasticsearch indexing rules for IIIF manifests"""

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer
from django.utils.html import strip_tags
from unidecode import unidecode

from apps.iiif.kollections.models import Collection
from .models import Manifest

# TODO: Better English stemming (e.g. Rome to match Roman), multilingual stemming.
html_strip_and_stem = analyzer(
    "html_strip",
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball", "porter_stem"],
    char_filter=["html_strip"]
)


@registry.register_document
class ManifestDocument(Document):
    """Elasticsearch Document class for IIIF Manifest"""

    # fields to map explicitly in Elasticsearch
    authors = fields.KeywordField(multi=True)  # only used for faceting/filtering
    author = fields.TextField()  # only used for searching
    collections = fields.NestedField(properties={
        "label": fields.KeywordField(),
    })
    date_earliest = fields.DateField()
    date_latest = fields.DateField()
    has_pdf = fields.BooleanField()
    label = fields.TextField(analyzer=html_strip_and_stem)
    label_alphabetical = fields.KeywordField()
    languages = fields.KeywordField(multi=True)
    summary = fields.TextField(analyzer=html_strip_and_stem)

    class Index:
        """Settings for Elasticsearch"""
        name = "manifests"

    class Django:
        """Settings for automatically pulling data from Django"""
        model = Manifest

        # fields to map dynamically in Elasticsearch
        fields = [
            "attribution",
            "created_at",
            "date_sort_ascending",
            "date_sort_descending",
            "license",
            "pid",
            "published_city",
            "published_date",
            "publisher",
            "viewingdirection",
        ]
        related_models = [Collection]

    def prepare_authors(self, instance):
        """convert authors string into list"""
        if instance.author:
            return [s.strip() for s in instance.author.split(";")]
        return ["[no author]"]

    def prepare_has_pdf(self, instance):
        """convert pdf field into boolean"""
        return bool(instance.pdf)

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

    def prepare_summary(self, instance):
        """Strip HTML tags from summary"""
        return strip_tags(instance.summary)

    def get_queryset(self):
        """prefetch related to improve performance"""
        return super().get_queryset().prefetch_related(
            "collections"
        )

    def get_instances_from_related(self, related_instance):
        """Retrieving item to index from related collections"""
        if isinstance(related_instance, Collection):
            # many to many relationship
            return related_instance.manifests.all()
