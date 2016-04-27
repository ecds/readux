from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse

from readux.utils import solr_interface
from readux.books.models import Volume, Page

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
    # priority uncertain;
    # default priority is 0.5; set PDFs slightly lower
    priority = 0.4


    def location(self, item):
        return reverse('books:pdf', kwargs={'pid': item['pid']})


class VolumeSitemap(_BaseVolumeSitemap):
    # priority unknown

    def location(self, item):
        return reverse('books:volume', kwargs={'pid': item['pid']})


class VolumePageSitemap(Sitemap):
    'Sitemap for individual pages'

    # default priority is 0.5; set pages slightly lower
    priority = 0.4

    def items(self):
        solr = solr_interface()
        return solr.query(content_model=Page.PAGE_CMODEL_PATTERN) \
                   .field_limit(['pid', 'last_modified',
                                 'isConstituentOf'])

    def lastmod(self, item):
        return item['last_modified']

    def location(self, item):
        # volume page belongs to is indexed based on fedora relation
        vol_pid = item['isConstituentOf'][0].replace('info:fedora/', '')
        return reverse('books:page',
                       kwargs={'pid': item['pid'], 'vol_pid': vol_pid})
