from modeltranslation.translator import register, TranslationOptions
from .models import Collection

@register(Collection)
class CollectionsTranslationOptions(TranslationOptions):
    fields = ('label', 'summary',)
