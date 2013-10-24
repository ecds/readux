from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model; User = get_user_model()
from django.utils.translation import ugettext as _

from toolware.utils.mixin import CleanSpacesMixin

import defaults


class UserPersonalForm(CleanSpacesMixin, forms.ModelForm):
    
    required_css_class = 'required_field'

    def __init__(self, *args, **kwargs):
        super(UserPersonalForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    class Meta:
        model = User
        fields = (
                'first_name',
                'last_name',
                'about',
        )

class UserPreferencesForm(CleanSpacesMixin, forms.ModelForm):
    
    required_css_class = 'required_field'

    class Meta:
        model = User
        fields = (
                'email_privacy',
                'is_public',
                'is_search_engine_friendly',
        )


