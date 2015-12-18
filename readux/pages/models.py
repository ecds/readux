from django.db import models

# Create your models here.

from django.utils.translation import ugettext_lazy as _

from feincms.module.page.models import Page
from feincms.content.richtext.models import RichTextContent
from feincms.content.medialibrary.models import MediaFileContent
from feincms.content.video.models import VideoContent

# Page.register_extensions('datepublisher', 'translations') # Example set of extensions
# Page.register_extensions('changedate')  # in docs but not available

Page.register_templates({
    'title': _('Standard template'),
    'path': 'pages/base.html',
    'regions': (
        ('main', _('Main content area')),
        # ('sidebar', _('Sidebar'), 'inherited'),
        ),
    })

Page.create_content_type(RichTextContent)
Page.create_content_type(MediaFileContent, TYPE_CHOICES=(
    ('default', _('default')),
    ('lightbox', _('lightbox')),
    ))

Page.create_content_type(VideoContent)