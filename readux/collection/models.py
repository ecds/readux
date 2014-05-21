import re

from eulcm.models.collection.v1_0 import Collection as Collectionv1_0


class Collection(Collectionv1_0):
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

