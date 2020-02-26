from django.dispatch import receiver
from allauth.socialaccount.signals import pre_social_login
from allauth.socialaccount.models import SocialLogin
from allauth.account.models import EmailAddress
import logging

logger = logging.getLogger(__name__)

# allauth.socialaccount.signals.pre_social_login(request, sociallogin)
@receiver(pre_social_login, sender=SocialLogin)
def  check_if_exists(sender, **kwargs):
    logger.debug("******************* {e}".format(e=kwargs.keys()))
    existing = EmailAddress.objects.get(email=kwargs['email_addresses'][0])