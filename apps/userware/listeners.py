import sys
from django.conf import settings
from django.db.models import signals as django_db_signals
from django.contrib.auth import get_user_model; User = get_user_model()
from django.contrib.auth import models as auth_app
from django.contrib.auth.management import create_superuser as django_create_superuser

import defaults

def disable_superuser_request():
    # disable syncdb from prompting to create a superuser.
    # if we need a superuser, so we create it automatically
    django_db_signals.post_syncdb.disconnect(
        django_create_superuser,
        sender=auth_app,
        dispatch_uid = "django.contrib.auth.management.create_superuser"
    )

def _create_superuser(username, email, password):
    """
    Create or update and account of type supersuer (likely the first user of this site)
    """
    if username and email and password:
        user, created = User.objects.get_or_create(pk=defaults.USERWARE_SUPERUSER_ID)
        if user:
            user.username = username
            user.email = email
            user.set_password(password)
            user.is_staff = True
            user.is_active = True
            user.is_superuser = True
            user.save()
            action = "Created" if created else "Updated"
            print >> sys.stderr, "%s Superuser: [username=%s, email=%s, id=%d]" % (action, username, email, user.id)


# run only after the completion of syncdb
def custom_create_superuser(sender, **kwargs):
    """ After syncdb, finalize the required adjustements in order to prepare and secure the site """

    # only trigger if we have installed the last app
    if kwargs['app'].__name__ == '{0}.models'.format(settings.INSTALLED_APPS[-1]):

        # setup or update superuser
        _create_superuser(
            username=defaults.USERWARE_SUPERUSER_USERNAME,
            email=defaults.USERWARE_SUPERUSER_EMAIL,
            password=defaults.USERWARE_SUPERUSER_PASSWORD,
        )


# disable syncdb from prompting to create a superuser as we create it automatically
disable_superuser_request()

# enable custom user creation
django_db_signals.post_syncdb.connect(custom_create_superuser)



