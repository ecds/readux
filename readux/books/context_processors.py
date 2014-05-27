from readux.books.forms import BookSearch


def book_search(request):
    '''Template context processor: add book search form
    (:class:`~readux.books.forms.BookSearch`) to context so it can be
    used on any page.'''
    return  {
        'search_form': BookSearch()
    }
