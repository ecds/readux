import re
from django import forms
from django.utils.html import mark_safe
from eulcommon.searchutil import search_terms

class BookSearch(forms.Form):
    '''Form for searching books.'''
    #: keyword
    keyword = forms.CharField(required=True, label='Keyword',
            help_text=mark_safe('Search for content by keywords or exact phrase (use quotes). ' +
                      'Wildcards <b>*</b> and <b>?</b> are supported.'),
            error_messages={'required': 'Please enter one or more search terms'})


    def search_terms(self):
        '''Get a list of keywords and phrases from the keyword input field,
        using :meth:`eulcommon.searchutil.search_terms`.  Assumes that the form
        has already been validated and cleaned_data is available.'''
        # get list of keywords and phrases
        keywords = self.cleaned_data['keyword']
        # NOTE: currently using searchutil.search_terms to separate out
        # single words and exact phrases.  Because it also looks for
        # fielded search terms (like title:something or title:"another thing")
        # it can't handle searching on an ARK URI.  As a workaround,
        # encode known colons that should be preserved before running
        # search terms, and then restore them after.

        keywords = re.sub(r'(http|ark):', r'\1;;', keywords)
        return [re.sub(r'(http|ark);;', r'\1:', term)
               for term in search_terms(keywords)]


class VolumeExport(forms.Form):
    #: which readux page should be 1 in the exported volume
    page_one = forms.IntegerField(
        label="Start Page", min_value=1, required=False,
        help_text='Select the page in the Readux that should be the first ' +
        ' numbered page in your digital edition. Preceding pages will ' +
        ' be numbered with a prefix, and can be customized after export.' +
        ' (Optional)')
    #: annotations to export: individual or group
    annotations = forms.ChoiceField(
        label='Annotations to export',
        help_text='Individual annotations or all annotations shared with ' +
        'a single group')

    #: export mode
    mode = forms.ChoiceField(
        label='Export mode',
        choices=[
            ('jekyll', 'Download'),
            ('github', 'Publish on GitHub'),
            ('github_update', 'Update existing Github repo')
        ],
        widget=forms.RadioSelect,
        help_text='Choose how to export your volume as a Jekyll site.'
    )
    #: help text for export mode choices
    mode_help = [
        'Download a new Jekyll site as a zip file',
        '''Create a new GitHub repository with the generated Jekyll
                site content and publish it using Github Pages''',
        'Update existing GitHub repo'
    ]

    #: github repository name to be created
    github_repo = forms.SlugField(
        label='GitHub repository name',
        help_text='Name of the repository to be created, which will also ' +
        'determine the GitHub pages URL.')
    #: github repository to be updated, if update is selected
    update_repo = forms.CharField(
        label='GitHub repository to update',
        help_text='Existing repository to be updated')

    # flag to allow suppressing annotation choice display when
    # user does not belong to any annotation groups
    hide_annotation_choice = False

    def __init__(self, user, user_has_github=False, *args, **kwargs):
        self.user = user

        # initialize normally
        super(VolumeExport, self).__init__(*args, **kwargs)

        # set annotation choices and default
        self.fields['annotations'].choices = self.annotation_authors()
        self.fields['annotations'].default = 'user'
        # if user only has one choice for annotations, set hide flag
        if len(self.fields['annotations'].choices) == 1:
            self.hide_annotation_choice = True

        # if not user_has_github:
            # would be nice to mark github options as disabled
            # TODO: mark github radio button options as disabled

    def annotation_authors(self):
        # choices for annotations to be exported:
        # individual user, or annotations visible by group
        choices = [('user', 'Authored by me')]
        for group in self.user.groups.all():
            if group.annotationgroup:
                choices.append((group.annotationgroup.annotation_id,
                                'All annotations shared with %s' % group.name))
        return choices

