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


class VolumeExport(forms.Form):
    export_modes = ['static', 'jekyll']
    export_mode_choices = [(val, val) for val in export_modes]

    #: export mode - currently supports jekyll or static
    mode = forms.ChoiceField(choices=export_mode_choices, required=True,
        label="Export Mode")

    #: which readux page should be 1 in the exported volume
    page_one = forms.IntegerField(label="Start Page", min_value=1, required=False,
        help_text='Select the page in the Readux that should be the first '+ \
        ' numbered page in your digital edition. Preceding pages will ' + \
        ' be numbered with a prefix, and can be customized after export.' + \
        ' (Optional)')

    # NOTE: github export only makes sense with non-static mode, but
    # static export will hopefully be going away, so not implementing
    # additional form validation at this point.

    github = forms.BooleanField(label='Publish on GitHub',
        help_text='Create a new GitHub repository with the ' + \
        'generated Jekyll site content and publish it using Github Pages.',
        required=False)
    github_repo = forms.SlugField(label='GitHub repository name',
        help_text='Name of the repository to be created, which will also determine' + \
        ' the GitHub pages URL.')

