##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.conf import settings
from django.utils import timezone
from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import BaseUserManager
from django.core.files.storage import get_storage_class

from toolware.utils.generic import get_uuid
from toolware.utils.query import CaseInsensitiveUniqueManager
from slugify import slugify

from . import utils as util
from . import defaults as defs

EnabledLanguages = getattr(settings, 'ENABLED_LANGUAGES', {})
DefaultStorage = get_storage_class(defs.DEFAULT_FILE_STORAGE)


class UserProfileManager(CaseInsensitiveUniqueManager, BaseUserManager):
    """
    Custom User Manager Class.
    USERNAME_FIELD is the email field.
    """
    def _create_user(self, email, password, is_staff, is_superuser,
                     **extra_fields):
        """
        Creates and saves a User with the given, email and password.
        """
        if email:
            if password is None:
                # Social users have no passwords, but they can request one later on
                # via password reset.  We need to setup a random password since a usable
                # password is required by `has_usable_password()` to allow password resets.
                password = get_uuid(length=20, version=4)

            user = self.model(email=self.normalize_email(email),
                              is_staff=is_staff, is_active=True,
                              is_superuser=is_superuser,
                              last_login=timezone.now(),
                              **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
            return user
        else:
            # Translators: admin:skip
            raise ValueError(_('USER.EMAIL.REQUIRED'))

    def create_user(self, email=None, password=None, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)


class Profile(AbstractBaseUser, PermissionsMixin):
    """
    A custom user class w/ email & password as the only required fileds
    """

    default_storage = DefaultStorage()

    email = models.EmailField(
        # Translators: admin:skip
        _('USER.EMAIL'),
        db_index=True,
        unique=True,
        # Translators: admin:skip
        help_text=_('USER.EMAIL.DESC'),
    )

    is_superuser = models.BooleanField(
        # Translators: admin:skip
        _('USER.SUPERUSER'),
        default=False,
        # Translators: admin:skip
        help_text=_('USER.SUPERUSER.DESC'),
    )

    is_staff = models.BooleanField(
        # Translators: admin:skip
        _('USER.STAFF'),
        default=False,
        # Translators: admin:skip
        help_text=_('USER.STAFF.DESC'),
    )

    is_active = models.BooleanField(
        # Translators: admin:skip
        _('USER.ACTIVE'),
        default=True,
        # Translators: admin:skip
        help_text=_('USER.ACTIVE.DESC'),
    )

    # Django specific fields are above this line
    #############################################
    created_at = models.DateTimeField(
        # Translators: admin:skip
        _('USER.CREATED_AT'),
        default=timezone.now,
    )

    updated_at = models.DateTimeField(
        # Translators: admin:skip
        _('USER.UPDATED_AT'),
        auto_now=True,
    )

    first_name = models.CharField(
        # Translators: admin:skip
        _('USER.FIRST_NAME'),
        max_length=60,
        null=True,
        blank=False,
        # Translators: admin:skip
        help_text=_('USER.FIRST_NAME.DESC'),
    )

    last_name = models.CharField(
        # Translators: admin:skip
        _('USER.LAST_NAME'),
        max_length=255,
        null=True,
        blank=False,
        # Translators: admin:skip
        help_text=_('USER.LAST_NAME.DESC'),
    )

    is_verified = models.BooleanField(
        # Translators: admin:skip
        _('USER.VERIFIED'),
        default=False,
        # Translators: admin:skip
        help_text=_('USER.VERIFIED.DESC'),
    )

    photo = models.ImageField(
        # Translators: admin:skip
        _('USER.PHOTO'),
        null=True,
        blank=True,
        storage=default_storage,
        upload_to=util.uploadto_user_photo,
        max_length=255,
        # Translators: admin:skip
        help_text=_('USER.PHOTO.DESC'),
    )
    
    status = models.CharField(
        # Translators: admin:skip
        _('USER.STATUS'),
        default=defs.USER_STATUS_DEFAULT,
        choices=defs.USER_STATUS_CHOICES,
        max_length=60,
        # Translators: admin:skip
        help_text=_('USER.STATUS.DESC'),
    )

    language = models.CharField(
        # Translators: admin:skip
        _('USER.LANGUAGE'),
        max_length=40,
        default=defs.USER_DEFAULT_LANGUAGE,
        # Translators: admin:skip
        help_text=_('USER.LANGUAGE.DESC')
    )

    # ########## Add new fields above this line #############
    objects = UserProfileManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    CASE_INSENSITIVE_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        # Translators: admin:skip
        verbose_name = _('USER.LABEL')
        # Translators: admin:skip
        verbose_name_plural = _('USER.LABEL.PLURAL')

        permissions = (
            # ('add_profile', 'Can add new profile'),
            # ('change_profile', 'Can change all data on any profile'),
            # ('delete_profile', 'Can delete any non-superuser profile'),
            # ('view_profile', 'Can view public data on any profile'),
            ('read_profile', 'Can read all data on any profile'),
            ('update_profile', 'Can update public data on any profile'),
            ('switch_profile', 'Can switch to any non-superuser profile'),
        )

    def __str__(self):
        return '{} [{}]'.format(self.email, self.id)

    def get_username(self):
        """
        Return a unique user id instead of username 
        """
        return self.email
        
    def get_absolute_url(self):
        """
        Return public URL for user
        """
        return "/m/{}/{}".format(self.id, slugify(self.get_full_name()))

    def get_short_name(self):
        """
        Returns first name
        """
        return self.first_name

    def get_full_name(self):
        """
        Returns full name
        """
        return '{} {}'.format(self.first_name, self.last_name)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this user
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    # ########## Add new methods below this line #############
    @property
    def avatar(self):
        if self.photo and self.photo.url:
            return self.photo.url
        return None
