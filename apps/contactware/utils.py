import datetime
from django.utils import timezone

from ipware.ip import get_ip_address_from_request

from models import ContactMessage
import defaults


def check_email(email, from_host, from_email):
    """ Check the existance of an email address by contacting the provider """

    exists = True
    if not defaults.CONTACTWARE_VERIFY_EMAIL:
        return exists

    try:
        from spamware.email_check import email_exists
    except:
        return exists

    exists = email_exists(email, from_host, from_email)
    return exists


def check_spam(request, name, email, message):
    """ Check if the content is spam """

    spam = False
    if not defaults.CONTACTWARE_VERIFY_SPAM:
        return spam

    try:
        from spamware.spam_check import check_spam
    except:
        return spam

    spam = check_spam(request, name, email, message)
    return spam


def daily_message_limit_reached(request):
    """ returns True if max message number has been reached by ip_address """

    now = timezone.now()
    one_day = datetime.timedelta(days=1)
    yesterday = now - one_day
    tomorrow = now + one_day
    ip_address = get_ip_address_from_request(request)
    total_messages_today = ContactMessage.objects.filter(ip_address=ip_address,
                            created_at__gt=yesterday, created_at__lt=tomorrow)

    if len(total_messages_today) >= defaults.CONTACTWARE_TOTAL_DAILY_MESSAGES_BY_IP:
        return True
    return False


def clean_expired_contacts():
    """ Remove expired contact messages from the database """

    now = timzeone.now()
    expiration_date = datetime.timedelta(days=defaults.CONTACTWARE_EXPIRY_DAYS)
    contacts = ContactMessage.objects.all()
    for contact in contacts:
        if contact.created_at + expiration_date < now:
            contact.delete()



