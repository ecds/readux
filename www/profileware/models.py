import datetime, string
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.db.models import signals
from django.contrib.auth import get_user_model; User = get_user_model()
from django.utils.translation import gettext as _
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.core.cache import cache

from uuslug import slugify
from django.utils.functional import lazy


import defaults

class UserProfile(models.Model):
    """ Each user gets a profile automatically."""

    user = models.OneToOneField(User, related_name="%(class)s", unique=True)

    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    username = models.CharField(
                _("Username"), 
                max_length=32, 
                blank=True,
                editable=False,
    )

    first_name = models.CharField(
                _("First Name"),
                max_length=58,
                help_text=_('Your first name. (what your friends call you)'),
                blank=False,
    )

    last_name = models.CharField(
                _("Last Name"), 
                max_length=58, 
                help_text=_('Your last name, also known as surname or family name.'),
                blank=False,
    )

    slug = models.CharField(
                _("Slug"), 
                max_length=50, 
                blank=True,
                editable=False,
    )

    personal_about = models.TextField(
                _('About (Your Bio)'), 
                blank=True, 
                validators=[MaxLengthValidator(1000)],
                help_text = _("Tell others a little about youself. (highly recommended)")
    )

    primary_email = models.CharField(
                max_length=254,
                blank=True,
                editable=False,
    )

    def __unicode__(self):
        return self.get_full_name()

    def get_absolute_url(self):
        return "/%s/" % (self.username)

    def get_full_name(self):
        return u'{0} {1}'.format(self.first_name, self.last_name)

    def _sync_user_info(self):
        user_info_changed = False
        if self.first_name and self.first_name != self.user.first_name:
            self.user.first_name = self.first_name
            user_info_changed = True
        if self.last_name and self.last_name != self.user.last_name:
            self.user.last_name = self.last_name
            user_info_changed = True
        if not self.primary_email and self.user.email:
            self.primary_email = self.user.email
            user_info_changed = True
        if user_info_changed:
            self.user.save()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.get_full_name())
        self._sync_user_info()
        super(UserProfile, self).save(*args, **kwargs)


# Create a profile on demand if not already created
User.profile = property(lambda self: UserProfile.objects.get_or_create(user=self)[0])



