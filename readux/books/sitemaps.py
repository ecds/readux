from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse

from readux.utils import solr_interface
from readux.books.models import Volume

class _BaseVolumeSitemap(Sitemap):
    # common items/lastmodification logic for volumes and volume pdfs
    # volume change frequency unknown

    def items(self):
        solr = solr_interface()
        return solr.query(content_model=Volume.VOLUME_CMODEL_PATTERN) \
                   .field_limit(['pid', 'last_modified'])

    def lastmod(self, item):
        return item['last_modified']


class VolumePdfSitemap(_BaseVolumeSitemap):
    # priority unknown

    def location(self, item):
        return reverse('books:pdf', kwargs={'pid': item['pid']})


class VolumeSitemap(_BaseVolumeSitemap):
    # priority unknown

    def location(self, item):
        return reverse('books:volume', kwargs={'pid': item['pid']})