from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import condition
from urllib import urlencode

from eulcommon.searchutil import search_terms
from eulfedora.server import Repository, RequestFailed
from eulfedora.views import raw_datastream, datastream_etag

from readux.books.models import Volume
from readux.books.forms import BookSearch
from readux.utils import solr_interface

def search(request):

    form = BookSearch(request.GET)
    context = {'form': form}

    if form.is_valid():
        kw = form.cleaned_data['keyword']
        # get list of keywords and phrases
        terms = search_terms(kw)
        solr = solr_interface()
        q = solr.query().filter(content_model=Volume.VOLUME_CONTENT_MODEL) \
                .query(*terms) \
                .field_limit(['pid', 'title', 'label'], score=True)

        # paginate the solr result set
        paginator = Paginator(q, 30)
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        try:
            results = paginator.page(page)
        except (EmptyPage, InvalidPage):
            results = paginator.page(paginator.num_pages)

        # url parameters for pagination links
        url_params = request.GET.copy()
        if 'page' in url_params:
            del url_params['page']

        context.update({'items': results,
         'url_params': urlencode(url_params)})

    return render(request, 'books/search.html', context)


def pdf_etag(request, pid):
    return datastream_etag(request, pid, Volume.pdf.id)

def pdf_lastmodified(request, pid):
    repo = Repository()
    try:
        # retrieve the object so we can use it to set the download filename
        obj = repo.get_object(pid, type=Volume)
        return obj.pdf.created
    except RequestFailed:
        pass


@condition(etag_func=pdf_etag, last_modified_func=pdf_lastmodified)
def pdf(request, pid):
    '''View to allow access the PDF datastream of a
    :class:`~readux.books.models.Volume` object.  Sets a
    content-disposition header that will prompt the file to be saved
    with a default title based on the object label.
    '''
    repo = Repository()
    try:
        # retrieve the object so we can use it to set the download filename
        obj = repo.get_object(pid, type=Volume)
        extra_headers = {
            # generate a default filename based on the object label
            'Content-Disposition': "filename=%s.pdf" % obj.label.replace(' ', '-')
        }
        # use generic raw datastream view from eulfedora
        return raw_datastream(request, pid, Volume.pdf.id, type=Volume,
           repo=repo, headers=extra_headers)
    except RequestFailed:
        raise Http404
