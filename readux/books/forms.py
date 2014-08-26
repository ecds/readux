from django import forms
from django.utils.html import mark_safe
from eulcommon.searchutil import search_terms

class BookSearch(forms.Form):
    '''Form for searching books.'''
    #: keyword
    keyword = forms.CharField(required=True, label='Keyword',
            help_text=mark_safe('Search for content by keywords or exact phrase (use quotes). ' +
                      'Wildcards <b>*</b> and <b>?</b> are supported.') ,
            error_messages={'required': 'Please enter one or more search terms'})

    def search_terms(self):
        '''Get a list of keywords and phrases from the keyword input field,
        using :meth:`eulcommon.searchutil.search_terms`.  Assumes that the form
        has already been validated and cleaned_data is available.'''
        # get list of keywords and phrases
        return search_terms(self.cleaned_data['keyword'])
