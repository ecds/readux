from django.db import models
from apps.iiif.annotations.models import AbstractAnnotation, Annotation

class UserAnnotation(AbstractAnnotation):
    start_selector = models.ForeignKey(Annotation, on_delete=models.CASCADE, null=True, related_name='start_selector', default=None)
    end_selector = models.ForeignKey(Annotation, on_delete=models.CASCADE, null=True, related_name='end_selector', default=None)
    start_offset = models.IntegerField(null=True, default=None)
    end_offset = models.IntegerField(null=True, default=None)

    def __is_text_annotation(self):
        return all([
            isinstance(self.end_offset, int),
            isinstance(self.start_offset, int),
            isinstance(self.start_selector, Annotation),
            isinstance(self.end_selector, Annotation)
        ])

    @property
    def item(self):
        if self.__is_text_annotation():
            return dict({
                    'start_element': str(self.start_selector.pk),
                    'end_element': str(self.end_selector.pk),
                    'start_offset': self.start_offset,
                    'end_offset': self.end_offset
                })
        else:
            return None
