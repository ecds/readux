from django.shortcuts import render

from readux.utils import solr_interface
from readux.collection.models import Collection


def site_index(request):
    # placeholder index page (probably shouldn't be in readux.collection)
    return render(request, 'site_base.html')

def browse(request):
    solr = solr_interface()
    # FIXME: this filter should probably be commonly used across all LSDI
    # search and browse
    results = solr.query().filter(owner='LSDI-project') \
                .query(content_model=Collection.COLLECTION_CONTENT_MODEL) \
                .sort_by('title')

    # TODO: would be nice if we could use a facet or join query to get
    # a count of the number of volumes in a collection

    return render(request, 'collection/browse.html',
        {'collections': results})