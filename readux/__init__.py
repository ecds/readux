__version_info__ = (1, 6, 1, None)


# Dot-connect all but the last. Last is dash-connected if not None.
__version__ = '.'.join([str(i) for i in __version_info__[:-1]])
if __version_info__[-1] is not None:
    __version__ += ('-%s' % (__version_info__[-1],))


# context processor to add version to the template environment
def context_extras(request):
    socialauth_providers = []
    # generate a list of social auth providers associated with this account,
    # for use in displaying available backends
    if not request.user.is_anonymous():
        socialauth_providers = [auth.provider for auth in request.user.social_auth.all()]
    return {
        # software version
        'SW_VERSION': __version__,
        # Alternate names for social-auth backends,
        # to be used for display and font-awesome icon (lowercased)
        # If not entered here, backend name will be used as-is for
        # icon and title-cased for display (i.e., twitter / Twitter).
        'backend_names': {
            'github': 'GitHub',
            'google-oauth2': 'Google',
        },
        'user_socialauth_providers': socialauth_providers
    }

