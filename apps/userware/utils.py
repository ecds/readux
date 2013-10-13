from django.utils import timezone
from django.contrib.auth import get_user_model; User = get_user_model()

from datetime import datetime

from toolware.utils.generic import is_valid_email

def get_user_by_username_or_email(username_or_email):
    """ Returns a user given an email or username"""
    try:
        if is_valid_email(username_or_email):
            user = User.objects.get(email__iexact=username_or_email)
        else:
            user = User.objects.get(username__iexact=username_or_email)
    except User.DoesNotExist:
        try:
            from emailware.models import EmailAddress
            user = EmailAddress.objects.get(email__iexact=username_or_email).user
        except:
            return None
    return user




