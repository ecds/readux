from django.conf import settings
from django.core.urlresolvers import reverse

from social.apps.django_app.middleware import SocialAuthExceptionMiddleware
from social.exceptions import AuthAlreadyAssociated


class LocalSocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    # Extend the default social auth middleware to add
    # a special case for the account already in use error,
    # so that we can redirect to a custom error page

    def raise_exception(self, request, exception):
        # if error is auth already associated, don't raise it,
        # even in debug mode
        if isinstance(exception, AuthAlreadyAssociated):
            return False
        return super(LocalSocialAuthExceptionMiddleware, self) \
                    .raise_exception(request, exception)

    def get_redirect_uri(self, request, exception):
        # if exception is auth already associated, redirect
        # to local custom error page to explain the error
        if isinstance(exception, AuthAlreadyAssociated):
            return reverse('accounts:error')
        return super(LocalSocialAuthExceptionMiddleware, self) \
                    .get_redirect_uri(request, exception)
