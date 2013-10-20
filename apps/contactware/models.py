from django.db import models
from django.utils.translation import gettext as _
from django.core.validators import MinLengthValidator
from django.core.validators import MaxLengthValidator

class ContactMessage(models.Model):
    """ Contact Message Model """

    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    name = models.CharField(
                _("Your name"), 
                max_length=120, 
                blank=False,
    )

    email = models.EmailField(
                _('Your email address'), 
                max_length=250, 
                blank=False,
    )

    subject = models.CharField(
                _("Message Subject"),
                max_length=120,
                blank=False,
    )

    message = models.TextField(
                _('Your message'), 
                blank=False, 
                validators=[MinLengthValidator(10), MaxLengthValidator(750)],
    )

    referrer = models.CharField(_('referrer'), max_length=254, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __unicode__(self):
        return u'{}-{}-{}'.format(self.name, self.email, self.ip_address)



