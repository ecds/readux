from django import forms

class BookSearch(forms.Form):
    '''Form for searching books.'''
    #: keyword
    keyword = forms.CharField(required=True, label='Keyword',
            help_text='Search for content by keywords or exact phrase (use quotes).</br>' +
                      'Wildcards <b>*</b> and <b>?</b> are supported.',
          error_messages={'required': 'Please enter one or more search terms'})
