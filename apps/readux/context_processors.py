from . import __version__

def current_version(request=None):
    return {'APP_VERSION': __version__}
