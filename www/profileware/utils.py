from django.core.cache import cache
from django.contrib.sites.models import Site

import defaults

def load_user_profile(request, instance):
    """ Try load user profile from memory first, or from db """

    if request.user == instance.user:
        return request.user.profile
    return instance.user.profile
