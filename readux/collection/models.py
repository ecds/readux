import re
from UserDict import UserDict
from django.db import models
from django_image_tools.models import Image

from eulcm.models.collection.v1_0 import Collection as Collectionv1_0
from readux.utils import solr_interface


class BaseCollection(object):
    '''Common functionality for :class:`Collection` and :class:`SolrCollection`'''

    @property
    def images(self):
        'associated :class:`CollectionImage` if there is one for this pid'
        try:
            return CollectionImage.objects.filter(collection=self.pid).get()
        except CollectionImage.DoesNotExist:
            pass

    @property
    def cover(self):
        'cover image for associated :class:`CollectionImage`, if available'
        if self.images:
            return self.images.cover

    @property
    def banner(self):
        'cover image for associated :class:`CollectionImage`, if available'
        if self.images:
            return self.images.banner


class Collection(Collectionv1_0, BaseCollection):
    '''Fedora Collection Object.  Extends
    :class:`~eulcm.models.collection.v1_0.Collection`.
    '''
    #: common label prefix on all collections
    LABEL_PREFIX = 'Large-Scale Digitization Initiative \(LSDI\) -'
    #: common label suffix on all collections
    LABEL_SUFFIX = 'Collection'

    @property
    def short_label(self):
        '''The label of the collection with
        :attr:`LABEL_PREFIX` and :attr:`LABEL_SUFFIX` removed.
        '''
        # remove prefix at the beginning, suffix at the end, strip any outer whitespace
        short_label = re.sub('^%s' % self.LABEL_PREFIX, '', self.label.strip())
        return re.sub('%s$' % self.LABEL_SUFFIX, '', short_label).strip()

    def index_data(self):
        data = super(Collection, self).index_data()
        # replace full title with short label
        data['title'] = self.short_label
        return data


class SolrCollection(UserDict, BaseCollection):
    '''Extension of :class:`~UserDict.UserDict` for use with Solr results
    for volume-specific content.  Extends :class:`BaseCollection` for common
    collection logic (specifically access to related images).
    '''

    def __init__(self, **kwargs):
        # sunburnt passes fields as kwargs; userdict wants them as a dict
        UserDict.__init__(self, kwargs)

    @property
    def pid(self):
        'object pid'
        return self.data.get('pid')


def collection_choices():
    'collection choices (pid and title) for :attr:`CollectionImage.collection`'
    solr = solr_interface()
    results = solr.query(content_model=Collection.COLLECTION_CONTENT_MODEL) \
          .filter(owner='LSDI-project') \
          .sort_by('title_exact')  \
          .field_limit(['pid', 'title'])

    choices = [(r['pid'], r['title']) for r in results]
    return choices


class CollectionImage(models.Model):
    # NOTE: collection field should be selected from fedora lsdi collections;
    # stores the pid, but displays the collection label to the user
    collection = models.CharField(max_length=255, unique=True, choices=[])
    cover = models.ForeignKey(Image, related_name='coverimage_set')
    banner = models.ForeignKey(Image, blank=True, null=True,
                               related_name='bannerimage_set')

    def __init__(self, *args, **kwargs):
       super(CollectionImage, self).__init__(*args, **kwargs)
       # set collection choices at first class init instead of load time
       # (only load when needed, make it possible to mock solr for tests)
       collection_field = self._meta.get_field_by_name('collection')[0]
       if not collection_field._choices:
            collection_field._choices = collection_choices()

    @property
    def collection_label(self):
        # get collection label from solr via pid
        solr = solr_interface()
        results = solr.query(pid=self.collection).field_limit('title')
        if results:
            return results[0]['title']
        else:
            # return collection pid as fallback if lookup title fails
            return self.collection

    # NOTE: borrowing special properties from Image to make thumbnails
    # displayable in django admin

    @property
    def cover_thumbnail(self):
        if self.cover:
            return self.cover.thumbnail

    @property
    def banner_thumbnail(self):
        if self.banner:
            return self.banner.thumbnail
