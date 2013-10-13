from django.contrib.auth.backends import ModelBackend as DjangoModelBackend
from utils import get_user_by_username_or_email


class ModelBackend(DjangoModelBackend):
    """ Authenticates user against username or email address"""
        
    # check if this is an email-based authenticaiton
    def authenticate(self, username=None, password=None):
        user = get_user_by_username_or_email(username)
        if user and user.check_password(password):
            return user
        return None



