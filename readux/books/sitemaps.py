from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse

from readux.utils import solr_interface
from readux.books.models import Volume

class VolumePdfSitemap(Sitemap):
    # change frequency & priority unknown

    def items(self):
        solr = solr_interface()
        return solr.query(content_model=Volume.VOLUME_CONTENT_MODEL) \
                   .field_limit(['pid', 'last_modified'])

    def location(self, item):
        return reverse('books:pdf', kwargs={'pid': item['pid']})

    def lastmod(self, item):
        return item['last_modified']
