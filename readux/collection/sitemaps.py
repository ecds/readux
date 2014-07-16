from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse

from readux.utils import solr_interface
from readux.collection.models import Collection

class CollectionSitemap(Sitemap):
    # change frequency & priority unknown

    def items(self):
        solr = solr_interface()
        return solr.query(content_model=Collection.COLLECTION_CONTENT_MODEL) \
                   .filter(owner='LSDI-project') \
                   .sort_by('title_exact') \
                   .field_limit(['pid', 'last_modified'])

    def location(self, item):
        return reverse('collection:view', kwargs={'pid': item['pid']})

    def lastmod(self, item):
        return item['last_modified']
