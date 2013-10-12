from django.conf import settings

from sites import setup_sites
import defaults

# run only after the completion of syncdb
def finalize(sender, **kwargs):
    """
    After syncdb, finalize the required adjustements in order to prepare and secure the site
    """
    # only trigger if we have installed the last app
    if kwargs['app'].__name__ == '{0}.models'.format(settings.INSTALLED_APPS[-1]):

        # setup sites
        setup_sites()

        # do other site-wide related stuff here