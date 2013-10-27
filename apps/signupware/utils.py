from django.contrib.sites.models import Site

import defaults

def check_email(email):
    """ Check the existance of an email address by contacting the email provider """

    exists = True
    if not defaults.SIGNUPWARE_VERIFY_EMAIL:
        return exists

    if not defaults.SIGNUPWARE_SPAMWARE_INSTALLED:
        return exists

    try:
        from spamware.email_check import email_exists
    except:
        return exists

    from_host = Site.objects.get_current().domain
    from_email = 'verify@{0}'.format(from_host)
    exists = email_exists(email, from_host, from_email)
    return exists



