__version_info__ = (1, 3, 2, None)


# Dot-connect all but the last. Last is dash-connected if not None.
__version__ = '.'.join([str(i) for i in __version_info__[:-1]])
if __version_info__[-1] is not None:
    __version__ += ('-%s' % (__version_info__[-1],))


# context processor to add version to the template environment
def context_extras(request):
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
    }

