from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model; User = get_user_model()
from django.utils.translation import ugettext as _

from toolware.utils.mixin import CleanSpacesMixin

from models import UserProfile
import defaults


class UserProfileForm(CleanSpacesMixin, forms.ModelForm):
    
    required_css_class = 'required_field'

    class Meta:
        model = UserProfile
        fields = (
                'first_name',
                'last_name',
                'personal_about',
        )


