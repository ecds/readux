import re
from django import forms
from django.utils.html import mark_safe
from eulcommon.searchutil import search_terms


# add is_checkbox method to all form fields, to enable template logic.
# thanks to:
# http://stackoverflow.com/questions/3927018/django-how-to-check-if-field-widget-is-checkbox-in-the-template
setattr(forms.Field, 'is_checkbox',
        lambda self: isinstance(self.widget, forms.CheckboxInput))


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
    #: export mode
    mode = forms.ChoiceField(
        label='Export mode',
        choices=[
            ('tei', 'Download TEI facsimile with annotations'),
            ('download', 'Download Jekyll site'),
            ('github', 'Publish Jekyll site on GitHub'),
            ('github_update', 'Update an existing Github repo')
        ],
        initial='download',
        widget=forms.RadioSelect,
        help_text='Choose how to export your annotated volume.'
    )
    #: help text for export mode choices
    mode_help = [
        'Download a TEI XML file with facsimile volume data and annotations',
        'Download a zip file with all Jekyll site contents',
        '''Create a new GitHub repository with the generated Jekyll
            site content and publish it using Github Pages''',
        'Update a Jekyll site in an existing GitHub repo'
    ]

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

    #: include page images in export, instead of referencing on readux
    include_images = forms.BooleanField(
        label='Include page images in export package',
        help_text='By default, page images are served via Readux.  Enable this' +
        'option to make your site more functional as a standalone entity' +
        '(including images will make your site larger).',
        required=False)
    # NOTE: at some point in the future, option to include images may depend
    # on the rights and permissions for the individual volume, and might
    # not be available for all content that can be exported.

    deep_zoom = forms.ChoiceField(
        label='Deep zoom images',
        choices=[
            ('hosted', 'Hosted and served out via Readux / IIIF image server'),
            ('include', 'Include Deep Zoom images in export'),
            # To be added: no deep zoom
        ],
        initial='hosted',
        # NOTE: could structure like export mode, but requires extra
        # template work
        # widget=forms.RadioSelect,
        help_text='Deep zoom images can be included in your site to make ' +
        'the site more functional as a standalone entity, but it will make ' +
        'your site larger.  (Incuding deep zoom images is only allowed ' +
        'when page images are included.)'
        )

    #: github repository name to be created
    github_repo = forms.SlugField(
        label='GitHub repository name', required=False,
        help_text='Name of the repository to be created, which will also ' +
        'determine the GitHub pages URL.')
    #: github repository to be updated, if update is selected
    update_repo = forms.CharField(
        label='GitHub repository to update', required=False,
        help_text='Existing repository to be updated ' +
                  '(type to search and select from your GitHub repos). ' +
                  'If you specified a start page in your previous export, ' +
                  'you should specify the same one to avoid changes.')

    #: options that are relevant to jekyll export but not to TEI
    jekyll_options = ['page_one', 'include_images', 'deep_zoom']
    # used in the template to flag fields so javascript can hide them
    # when TEI export is selected

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

    def clean(self):
        cleaned_data = super(VolumeExport, self).clean()
        include_images = cleaned_data.get("include_images")
        deep_zoom = cleaned_data.get("deep_zoom")

        if deep_zoom == 'included' and not include_images:
            raise forms.ValidationError(
                'Including Deep Zoom images in your export requires that ' +
                ' you also include page images'
            )

    def annotation_authors(self):
        # choices for annotations to be exported:
        # individual user, or annotations visible by group
        choices = [('user', 'Authored by me')]
        for group in self.user.groups.all():
            if group.annotationgroup:
                choices.append((group.annotationgroup.annotation_id,
                                'All annotations shared with %s' % group.name))
        return choices

