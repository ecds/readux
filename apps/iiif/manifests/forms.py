from django import forms


# add is_checkbox method to all form fields, to enable template logic.
# thanks to:
# http://stackoverflow.com/questions/3927018/django-how-to-check-if-field-widget-is-checkbox-in-the-template
setattr(forms.Field, 'is_checkbox',
        lambda self: isinstance(self.widget, forms.CheckboxInput))



class JekyllExportForm(forms.Form):
    #: export mode
    mode = forms.ChoiceField(
        label='Export mode',
        choices=[
            ('download', 'Download Jekyll site export'),
            ('github', 'Publish Jekyll site on GitHub')
        ],
        initial='none',
        widget=forms.RadioSelect(attrs={'class': 'uk-radio'}),
        help_text='Choose how to export your annotated volume.'
    )
    #: help text for export mode choices
    mode_help = [
        'Download a zip file with all Jekyll site contents',
        '''Create or update a GitHub repository with the generated Jekyll
            site content and publish it using Github Pages'''
    ]

    # #: which readux page should be 1 in the exported volume
    # page_one = forms.IntegerField(
    #     label="Start Page", min_value=1, required=False,
    #     help_text='Optional: Select the page in the Readux that should be the first ' +
    #     ' numbered page in your digital edition. Preceding pages will ' +
    #     ' be numbered with a prefix, and can be customized after export.')
    #: annotations to export: individual or group
    # annotations = forms.ChoiceField(
    #     label='Annotations to export',
    #     help_text='Individual annotations or all annotations shared with ' +
    #     'a single group.')

    #: include page images in export, instead of referencing on readux
    # include_images = forms.BooleanField(
    #     label='Include page images in export package',
    #     help_text='By default, page images are served from the originating content provider.  Enable this' +
    #     'option to make your site more functional as a standalone entity' +
    #     '(including images will make your site larger).',
    #     required=False)

    # image_hosting = forms.ChoiceField(
    #     label='Image Hosting',
    #     choices=[
    #         ('readux_hosted', 'Host images via Readux / IIIF image server'),
    #         ('independently_hosted', 'Host images independently'),
    #     ],
    #     initial='readux_hosted',
    #     help_text='Whether page images are served via Readux or independently in the export (i.e. images in the Jekyll export download or on GitHub; including images will make site larger).'
    # )
    # NOTE: at some point in the future, option to include images may depend
    # on the rights and permissions for the individual volume, and might
    # not be available for all content that can be exported.

    # deep_zoom = forms.ChoiceField(
    #     label='Deep Zoom Images',
    #     choices=[
    #         ('include', 'Include Deep Zoom images in export'),
    #         ('exclude', 'Exclude Deep Zoom images from export'),
    #     ],
    #     required=False,
    #     initial='exclude',
    #     # NOTE: could structure like export mode, but requires extra
    #     # template work
    #     # widget=forms.RadioSelect,
    #     help_text='Deep zoom images can be included in your site to make ' +
    #     'the site more functional as a standalone entity, but it will make ' +
    #     'your site larger. (Including deep zoom images is only allowed ' +
    #     'when page images are included.) Deep zoom images can be excluded ' +
    #     'entirely so the exported site can standalone without including all ' +
    #     'the images and storage required for deep zoom.'
    #     )

    #: github repository name to be created
    github_repo = forms.SlugField(
        label='GitHub repository name', required=False,
        widget=forms.TextInput(attrs={'class': 'rdx-input uk-input'}),
        help_text='Name of the repository to be created or updated, which will also ' +
        'determine the GitHub pages URL.')
    # #: github repository to be updated, if update is selected
    # update_repo = forms.CharField(
    #     label='GitHub repository to update', required=False,
    #     help_text='Existing repository to be updated ' +
    #               '(type to search and select from your GitHub repos). ' +
    #               'If you specified a start page in your previous export, ' +
    #               'you should specify the same one to avoid changes.')

    #: options that are relevant to jekyll export but not to TEI
    jekyll_options = [
        # 'page_one', 
        # 'deep_zoom', 
        # 'image_hosting'
    ]
    # used in the template to flag fields so javascript can hide them
    # when TEI export is selected

    # flag to allow suppressing annotation choice display when
    # user does not belong to any annotation groups
    hide_annotation_choice = False

    def __init__(self, user, user_has_github=False, *args, **kwargs):
        self.user = user

        # initialize normally
        super(JekyllExportForm, self).__init__(*args, **kwargs)
        # If the person has not aughorized GitHub access, remove the GitHub
        # options and select download by default.
        if 'github' not in user.socialaccount_list:
            self.fields['mode'].choices = self.fields['mode'].choices[:1]
            self.fields['mode'].widget.attrs={'class': 'uk-radio', 'checked': True}
        # # set annotation choices and default
        # self.fields['annotations'].choices = self.annotation_authors()
        # self.fields['annotations'].default = 'user'
        # # if user only has one choice for annotations, set hide flag
        # if len(self.fields['annotations'].choices) == 1:
        #     self.hide_annotation_choice = True


    def clean(self):
        super(JekyllExportForm, self).clean()
        # image_hosting = cleaned_data.get("image_hosting")
        # deep_zoom = cleaned_data.get("deep_zoom")
        # mode = cleaned_data.get("mode")

        # if deep_zoom == "included" and not image_hosting == "independently_hosted":
        #     raise forms.ValidationError(
        #         'Including Deep Zoom images in your export requires that ' +
        #         ' you also include page images'
        #     )

    # def annotation_authors(self):
    #     # choices for annotations to be exported:
    #     # individual user, or annotations visible by group
    #     choices = [('user', 'Authored by me')]
    #     for group in self.user.groups.all():
    #         if group.annotationgroup:
    #             choices.append((group.annotationgroup.annotation_id,
    #                             'All annotations shared with %s' % group.name))
    #     return choices
