import logging
import sys
from django.conf import settings
from django.contrib.auth import models as auth_app
from django.db.models import signals as django_db_signals
from django.contrib.auth import signals as django_auth_signals
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model; User = get_user_model()
from django.contrib.auth.management import create_superuser as django_create_superuser

from ipware.ip import get_ip_address_from_request
from toolware.utils.generic import get_hashed

from models import UserAudit
from utils import cleanup_user_audits

import defaults
import constants

logger = logging.getLogger('userware.listeners')

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
    if kwargs['app'].__name__ == '{}.models'.format(settings.INSTALLED_APPS[-1]):

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



def user_audit_create(sender, user, request, **kwargs):
    """ Create a user  audit when user is logged in """

    audit_key = get_hashed(request.session.session_key)
    try:
        audit = UserAudit.objects.get(audit_key=audit_key)
    except UserAudit.DoesNotExist:
        data = {
            'user': request.user,
            'audit_key': audit_key,
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'ip_address': get_ip_address_from_request(request),
            'referrer': request.META.get('HTTP_REFERER', 'Unknown'),
            'last_page': request.path or '/',
        }
        audit = UserAudit(**data)
    logger.info(_('User {} logged in'.format(request.user.username)))
    audit.save()
    request.session[constants.USERWARE_AUDIT_KEY] = audit_key
    request.session.modified = True
    cleanup_user_audits(request.user)

# Latch on to login signal
django_auth_signals.user_logged_in.connect(user_audit_create, sender=User, 
                                     dispatch_uid='user_audit_create_call_me_only_once_please')


def user_audit_delete(sender, user, request, **kwargs):
    """ Delete a user  audit when user is logged out """

    try:
        UserAudit.objects.get(audit_key=request.session[constants.USERWARE_AUDIT_KEY]).delete()
    except:
        pass
    logger.info(_('User {} logged out'.format(request.user.username)))

# Latch on logout signal
django_auth_signals.user_logged_out.connect(user_audit_delete, sender=User,
                                       dispatch_uid='user_audit_delete_call_me_only_once_please')




