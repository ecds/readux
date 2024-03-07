"""Elasticsearch indexing rules for UserAnnotations"""

from html import unescape
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.utils.html import strip_tags

from apps.readux.models import UserAnnotation
from apps.iiif.manifests.documents import stemmer

@registry.register_document
class UserAnnotationDocument(Document):
    """Elasticsearch Document class for Readux UserAnnotation"""

    # fields to map explicitly in Elasticsearch
    canvas_index = fields.IntegerField()
    canvas_pid = fields.KeywordField()
    content = fields.TextField(analyzer=stemmer)
    manifest_pid = fields.KeywordField()
    owner_username = fields.KeywordField()
    pid = fields.KeywordField()

    class Index:
        """Settings for Elasticsearch"""

        name = "annotations"

    class Django:
        """Settings for automatically pulling data from Django"""

        model = UserAnnotation

    def prepare_content(self, instance):
        """Strip HTML tags from content"""
        return unescape(strip_tags(instance.content))

    def prepare_canvas_index(self, instance):
        return instance.canvas.position
    
    def prepare_canvas_pid(self, instance):
        return instance.canvas.pid

    def prepare_manifest_pid(self, instance):
        return instance.canvas.manifest.pid

    def prepare_owner_username(self, instance):
        return instance.owner.username
