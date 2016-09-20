from django.conf import settings
from django.db import models
from django.template import Context, Template
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
from random import shuffle

from feincms.module.page.models import Page
from feincms.content.richtext.models import RichTextContent
from feincms.content.medialibrary.models import MediaFileContent
from feincms.content.video.models import VideoContent

from readux.books.models import Volume
from readux.collection.models import Collection, SolrCollection
from readux.utils import solr_interface

# Page.register_extensions('datepublisher', 'translations') # Example set of extensions
# Page.register_extensions('changedate')  # in docs but not available

Page.register_templates({
    'title': _('Standard template'),
    'path': 'pages/base.html',
    'regions': (
        ('main', _('Main content area')),
        # ('sidebar', _('Sidebar'), 'inherited'),
        ('lead', _('Lead or tagline'), 'inherited'),
        ),
    })

Page.create_content_type(RichTextContent)
Page.create_content_type(MediaFileContent, TYPE_CHOICES=(
    ('default', _('default')),
    ('lightbox', _('lightbox')),
    ('responsive_embed_4by3.html', _('responsive_embed_4by3.html')),
    ))

Page.create_content_type(VideoContent)


class RandomCollectionContent(models.Model):
    num_collections = models.IntegerField()

    class Meta:
        abstract = True

    def render(self, **kwargs):
        # FIXME: lots of redundancy with collection list view
        solr = solr_interface()
        collq = solr.query(content_model=Collection.COLLECTION_CONTENT_MODEL) \
                    .results_as(SolrCollection)

        collection_owner = getattr(settings, 'COLLECTIONS_OWNER', None)
        if collection_owner:
            collq = collq.filter(owner=collection_owner)

        volq = solr.query(content_model=Volume.VOLUME_CMODEL_PATTERN) \
                   .facet_by('collection_id', sort='count', mincount=1) \
                   .paginate(rows=0)
        facets = volq.execute().facet_counts.facet_fields
        # convert into dictionary for access by pid
        collection_counts = dict([(pid, total) for pid, total in facets['collection_id']])
        # generate a list of tuple of solr result, volume count,
        # filtering out any collections with no items
        collections = [(r, collection_counts.get(r['pid'])) for r in collq
                       if r['pid'] in collection_counts]
        # randomize the order, then select the requested number for display
        shuffle(collections)
        collections = collections[:self.num_collections]

        tpl = get_template('pages/collection_list.html')
        return tpl.render({'collections': collections})

Page.create_content_type(RandomCollectionContent)
