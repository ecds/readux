"""Elasticsearch indexing rules for IIIF manifests"""

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer
from .models import Manifest

html_strip = analyzer(
    "html_strip",
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)

@registry.register_document
class ManifestDocument(Document):
    """Elasticsearch Document class for IIIF Manifest"""

    # fields to map explicitly in Elasticsearch
    authors = fields.TextField(multi=True)
    collections = fields.NestedField(properties={
        "summary": fields.TextField(analyzer=html_strip),
        "attribution": fields.TextField(),
        "pid": fields.TextField(),
        "label": fields.TextField(),
    })
    # TODO: date = DateRange()
    has_pdf = fields.BooleanField()
    # TODO: languages = fields.TextField()
    summary = fields.TextField(analyzer=html_strip)

    class Index:
        """Settings for Elasticsearch"""
        name = "manifests"

    class Django:
        """Settings for automatically pulling data from Django"""
        model = Manifest
        queryset_pagination = 25

        # fields to map dynamically in Elasticsearch
        fields = [
            "attribution",
            "label",
            "license",
            "pid",
            "published_city",
            "publisher",
            "viewingdirection",
        ]
        related_models = ["collections"]

    def prepare_authors(self, instance):
        """convert authors string into list"""
        if instance.author:
            return [s.strip() for s in instance.author.split(";")]
        return []

    def prepare_has_pdf(self, instance):
        """convert pdf field into boolean"""
        return bool(instance.pdf)

    def get_queryset(self):
        """prefetch related to improve performance"""
        return super().get_queryset().prefetch_related(
            "collections"
        )
