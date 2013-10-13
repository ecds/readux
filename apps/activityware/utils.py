import datetime
import hashlib
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model; User = get_user_model()

from models import UserActivityAudit
import constants

def get_audit_key(key):
    return hashlib.md5(key).hexdigest()


def get_logged_in_users(last_activity_in_minutes=5):
    """ Return all users with last activity less than `last_activity_in_minutes` ago."""

    last_active_delta = datetime.timedelta(minutes=last_activity_in_minutes)
    last_active = timezone.now() - last_active_delta
    query = Q(**{"useractivityaudit__updated_at__gte": last_active.isoformat()})
    related_fields = ['useractivityaudit__updated_at']
    users = User.objects.select_related(*related_fields).filter(query)
    return users


def get_sessions_for_user(user):
    """Returns all activity audit sessions for user"""

    uaa_sessions = UserActivityAudit.objects.filter(user=user)
    return uaa_sessions


def force_logout(user, request=None):
    """ logout all other sessions of this active user """

    uaa_sessions = get_sessions_for_user(user=user)
    for uaa in uaa_sessions:
        if request and uaa.audit_key == request.session.get(constants.ACTIVITYWARE_AUDIT_KEY, ''):
            uaa.force_logout = False
        else:
            uaa.force_logout = True
        uaa.save()

def cleanup_user_audits(user, audit_age_in_days=14):
    """ cleanup user audits that are older than  audit_age_in_days"""

    last_active_delta = datetime.timedelta(days=audit_age_in_days)
    last_active = timezone.now() - last_active_delta
    uaa_sessions = get_sessions_for_user(user=user)
    for uaa in uaa_sessions:
        if uaa.updated_at < last_active:
            uaa.delete()



