from django.db import models

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel

from .blocks import BaseStreamBlock


class ContentPage(Page):
    tagline = models.TextField(blank=True)
    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )

    content_panels = Page.content_panels + [
        FieldPanel('tagline', classname="full"),
        StreamFieldPanel('body'),
    ]
