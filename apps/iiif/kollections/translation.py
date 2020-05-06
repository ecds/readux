# This is not fully implamented. This will be a thing
# when v3 of the IIIF API is supported
"""Configuration for translating model fields."""
from modeltranslation.translator import register, TranslationOptions
from .models import Collection

@register(Collection)
class CollectionsTranslationOptions(TranslationOptions):
    """Register which fields to translate"""
    fields = ('label', 'summary',)
