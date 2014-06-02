from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import condition
from urllib import urlencode

from eulcommon.searchutil import search_terms
from eulfedora.server import Repository, RequestFailed
from eulfedora.views import raw_datastream, datastream_etag

from readux.books.models import Volume, SolrVolume
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
                .field_limit(['pid', 'title', 'label', 'language'], score=True) \
                .results_as(SolrVolume)

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
            'Content-Disposition': 'filename="%s.pdf"' % obj.label.replace(' ', '-')
        }
        # use generic raw datastream view from eulfedora
        return raw_datastream(request, pid, Volume.pdf.id, type=Volume,
            repo=repo, headers=extra_headers)
    except RequestFailed:
        raise Http404


def ocr_etag(request, pid):
    return datastream_etag(request, pid, Volume.ocr.id)

def ocr_lastmodified(request, pid):
    repo = Repository()
    try:
        # retrieve the object so we can use it to set the download filename
        obj = repo.get_object(pid, type=Volume)
        return obj.ocr.created
    except RequestFailed:
        pass


@condition(etag_func=ocr_etag, last_modified_func=ocr_lastmodified)
def text(request, pid):
    '''View to allow access the plain text content of a
    :class:`~readux.books.models.Volume` object.
    '''
    repo = Repository()
    obj = repo.get_object(pid, type=Volume)
    # if object doesn't exist, isn't a volume, or doesn't have ocr text - 404
    if not obj.exists or not obj.has_requisite_content_models or not obj.ocr.exists:
        raise Http404

    response = HttpResponse(obj.get_fulltext(), 'text/plain')
    # generate a default filename based on the object label
    response['Content-Disposition'] = 'filename="%s.txt"' % obj.label.replace(' ', '-')
    return response


def unapi(request):
    '''unAPI service point for :class:`~readux.books.models.Volume` objects,
    to make content available for harvest via Zotero.'''

    # NOTE: this could probably be generalized into a re-usable view
    # (maybe an extensible class-based view?) for re-use

    item_id = request.GET.get('id', None)
    format = request.GET.get('format', None)
    context = {}
    if item_id is not None:
        context['id'] = item_id
        repo = Repository(request=request)
        # generalized class-based view would need probably a get-item method
        # for repo objects, could use type-inferring repo variant
        obj = repo.get_object(item_id, type=Volume)

        formats = obj.unapi_formats

        if format is None:
            # display formats for this item
            context['formats'] = formats
        else:
            current_format = formats[format]
            # return requested format for this item
            meth = getattr(obj, current_format['method'])
            return HttpResponse(meth(), content_type=current_format['type'])

    else:
        # display formats for all items
        # NOTE: if multiple classes, should be able to combine the formats
        context['formats'] = Volume.unapi_formats

    # NOTE: doesn't really even need to be a template, could be generated
    # with eulxml just as easily if that simplifies reuse
    return render(request, 'books/unapi_format.xml', context,
        content_type='application/xml')

