"""Django Forms for export."""
from django import forms

# add is_checkbox method to all form fields, to enable template logic.
# thanks to:
# http://stackoverflow.com/questions/3927018/django-how-to-check-if-field-widget-is-checkbox-in-the-template
setattr(
    forms.Field,
    'is_checkbox',
    lambda self: isinstance(self.widget, forms.CheckboxInput)
)

class JekyllExportForm(forms.Form):
    """Form to provide export options."""
    #: export mode
    mode = forms.ChoiceField(
        label='Export mode',
        choices=[
            ('download', 'Download Jekyll site export'),
            ('github', 'Publish Jekyll site on GitHub'),
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

    #: github repository name to be created
    github_repo = forms.SlugField(
        label='GitHub repository name', required=False,
        widget=forms.TextInput(attrs={'class': 'rdx-input uk-input'}),
        help_text='Name of the repository to be created or updated, which will also ' +
        'determine the GitHub pages URL.')

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

    def __init__(self, user, *args, **kwargs):
        self.user = user

        # initialize normally
        super(JekyllExportForm, self).__init__(*args, **kwargs)
        # If the person has not authorized GitHub access, remove the GitHub
        # options and select download by default.
        if 'github' not in user.socialaccount_list:
            self.fields['mode'].choices = self.fields['mode'].choices[:1]
            self.fields['mode'].widget.attrs = {'class': 'uk-radio', 'checked': True}


    # def clean(self):
    #     super(JekyllExportForm, self).clean()
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
