from django.db.models import signals as django_signals
from django.contrib.auth import get_user_model; User = get_user_model()
from django.core.cache import cache

from models import UserProfile
######################################################################
def user_profile_create(sender, instance, created, **kwargs):
    """ Create a matching profile whenever a user object is created."""

    if created:
        try:
            p = UserProfile.objects.get_or_create(user=instance)[0]
        except:
            return
        p.username = p.user.username
        p.first_name = p.user.first_name
        p.last_name = p.user.last_name
        p.save()
django_signals.post_save.connect(
                    user_profile_create,
                    sender=User,
                    dispatch_uid='userprofile_create_call_me_only_once_please')

def user_profile_delete(sender, instance, **kwargs):
    """Delete a matching profile whenever a user object is deleted."""

    try:
        UserProfile.objects.get(user=instance).delete()
    except:
        pass
django_signals.pre_delete.connect(
                    user_profile_delete,
                    sender=User,
                    dispatch_uid='userprofile_delete_call_me_only_once_please')


######################################################################
from emailware.models import EmailAddress
from emailware import signals as email_signals

######################################################################
from emailware.models import EmailAddress
def email_saved_handler(sender, instance, created, **kwargs):
    """ Handle emails on post_save for this profile """

    p = instance.user.profile
    email = instance.email
    updated = False

    # primary email add only as we need one primary email at least
    if instance.is_default:
        p.primary_email = email
        updated = True

    # save if updated
    if updated:
        p.save()
django_signals.post_save.connect(
                    email_saved_handler,
                    sender=EmailAddress,
                    dispatch_uid='userprofile_email_saved_call_me_only_once_please')

def email_delete_handler(sender, instance, **kwargs):
    """ Handle emails on pre_delete for this profile """

    p = instance.user.profile
    email = ''
    updated = False
    if instance.is_default:
        p.primary_email = email
        updated = True
    if updated:
        p.save()
django_signals.pre_delete.connect(
                    email_delete_handler,
                    sender=EmailAddress,
                    dispatch_uid='userprofile_email_deleted_call_me_only_once_please')

######################################################################











