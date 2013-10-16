import re
from django.db import models
from django.utils import timezone
from django.core import validators
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager

try:
    from uuslug import slugify
except ImportError:
    from django.template.defaultfilters import slugify

USERNAME_PATTERN = re.compile('^[a-zA-Z0-9]+(-[a-zA-Z0-9]+)*$')

class ExtendedUser(AbstractBaseUser, PermissionsMixin):
    """ A drop-in replacement of Django User class that allows filed extensions """

    username = models.CharField(
            _('username'),
            max_length=30,
            unique=True,
            help_text=_("Username may only contain alphanumeric or dashes and cannot begin or end with a dash"),
            validators=[
                validators.RegexValidator(USERNAME_PATTERN, _('Enter a valid username.'), 'invalid')
            ]
    )

    first_name = models.CharField(
        _('first name'),
        max_length=30,
        blank=True,
    )

    last_name = models.CharField(
        _('last name'),
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        _('email address'),
        blank=True,
    )

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )

    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('User status. Inactive users cannot login. Treat as suspended user.'),
    )

    date_joined = models.DateTimeField(
        _('date joined'),
        default=timezone.now,
    )
    ############ Don't touch above this line ###############

    date_updated = models.DateTimeField(
        auto_now = True,
    )

    slug = models.CharField(
        _("Slug"),
        max_length=50,
        blank=True,
        editable=False,
    )

    about = models.TextField(
        _('About'), 
        blank=True, 
        validators=[MaxLengthValidator(1000)],
        help_text = _("Tell others a little about youself. (highly recommended)")
    )

    ########### Add new fields above this line #############
    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_absolute_url(self):
        """ User's URI """
        return "/%s/" % (self.username)

    def get_full_name(self):
        """ User's first and last name with space between """
        return u'{0} {1}'.format(self.first_name, self.last_name).strip()

    def get_short_name(self):
        """ User's first name """
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """ Sends an email to this User """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.get_full_name())
        super(ExtendedUser, self).save(*args, **kwargs)






