import logging
from django.contrib.auth import signals as django_signals
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model; User = get_user_model()

from ipware.ip import get_ip_address_from_request

from models import UserActivityAudit
from utils import get_audit_key
from utils import cleanup_user_audits

import constants

log = logging.getLogger('activityware.listeners')


def user_activity_audit_create(sender, user, request, **kwargs):
    """ Create a user activity audit when user is logged in """

    audit_key = get_audit_key(request.session.session_key)
    try:
        uaa = UserActivityAudit.objects.get(audit_key=audit_key)
    except UserActivityAudit.DoesNotExist:
        data = {
            'user': request.user,
            'audit_key': audit_key,
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'ip_address': get_ip_address_from_request(request),
            'referrer': request.META.get('HTTP_REFERER', 'Unknown'),
            'last_page': request.path or '/',
        }
        uaa = UserActivityAudit(**data)
    log.info(_('User {0} logged in'.format(request.user.username)))
    uaa.save()
    request.session[constants.ACTIVITYWARE_AUDIT_KEY] = audit_key
    request.session.modified = True
    cleanup_user_audits(request.user)

# Latch on to login signal
django_signals.user_logged_in.connect(user_activity_audit_create, sender=User, 
                                     dispatch_uid='user_activity_audit_create_call_me_only_once_please')


def user_activity_audit_delete(sender, user, request, **kwargs):
    """ Delete a user activity audit when user is logged out """

    try:
        UserActivityAudit.objects.get(audit_key=request.session[constants.ACTIVITYWARE_AUDIT_KEY]).delete()
    except:
        pass
    log.info(_('User {0} logged out'.format(request.user.username)))

# Latch on logout signal
django_signals.user_logged_out.connect(user_activity_audit_delete, sender=User,
                                       dispatch_uid='user_activity_audit_delete_call_me_only_once_please')



