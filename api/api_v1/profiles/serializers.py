##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

import logging

from django.conf import settings
from django.utils import six
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from django.core import exceptions
import django.contrib.auth.password_validation as validators

from rest_framework import serializers
from ..utils.common import get_url_name

log = logging.getLogger(__name__)
User = get_user_model()
AUTH_PASSWORD_LENGTH = getattr(settings, 'AUTH_PASSWORD_LENGTH', None)


class ProfileReadSerializerMixin(serializers.ModelSerializer):
    """ Profile serializer mixin """

    api_url = serializers.HyperlinkedIdentityField(lookup_field='pk',
        view_name=get_url_name(__name__, 'api-profile-retrieve'))

    photo_url = serializers.SerializerMethodField()

    def get_photo_url(self, obj):
        """ Return profile's photo URL """

        request = self.context.get('request')
        if obj.photo and obj.photo.url:
            return obj.photo.url
        return None


class ProfileReadAnonymousSerializer(ProfileReadSerializerMixin):
    """ Profile serializer: anonymous requests """

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'api_url',
            'photo_url',
        )


class ProfileReadAuthenticatedSerializer(ProfileReadSerializerMixin):
    """ Profile serializer: authenticated requests """

    email = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'api_url',
            'photo_url',
            'last_login',
            'updated_at',
            'created_at',
        )

    def get_email(self, obj):
        """ Return email if self/superuser is set """

        request = self.context.get('request')
        if request.user.is_superuser or request.user.id == obj.id:
            return obj.email
        return ''


class ProfileLoginSerializer(ProfileReadSerializerMixin):
    """ Profile serializer to return relevant data post login """

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'is_verified',
            'is_staff',
            'is_superuser',
            'api_url',
            'photo_url',
            'last_login',
            'updated_at',
            'created_at',
        )
        read_only_fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'is_verified',
            'is_staff',
            'is_superuser',
            'api_url',
            'photo_url',
            'last_login',
            'updated_at',
            'created_at',
        )


class ProfileCreateSerializer(ProfileLoginSerializer):
    """ Profile serializer for creating a user instance """

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'password',
            'first_name',
            'last_name',
            'is_verified',
            'is_staff',
            'is_superuser',
            'api_url',
            'photo_url',
            'last_login',
            'updated_at',
            'created_at',
        )
        read_only_fields = (
            'id',
            'last_login',
            'updated_at',
            'created_at',
            'is_verified',
            'is_staff',
            'is_superuser',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        """ Check if email is already in use """

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("EMAIL.IN_USE"))
        return value.lower()

    def validate(self, data):
        """ Validate Password """

        user = User(**data)
        password = data.get('password')
        errors = dict()
        try:
            validators.validate_password(password=password, user=User)
        except exceptions.ValidationError as e:
            errors['password'] = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(data)


class ProfileUpdateSerializer(ProfileReadSerializerMixin):
    """ Profile serializer for updating a user instance """

    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'is_verified',
            'api_url',
            'photo_url',
            'last_login',
            'updated_at',
            'created_at',
        )
        read_only_fields = (
            'id',
            'last_login',
            'updated_at',
            'created_at',
        )

    def validate_email(self, value):
        """ Check if email is already in use """

        request = self.context.get('request')
        if User.objects.filter(email__iexact=value).exclude(id=request.user.id).exists():
            raise serializers.ValidationError(_("EMAIL.IN_USE"))
        return value.lower()


class ProfilePasswordChangeSerializer(serializers.Serializer):
    """ Profile serializer for changing an account password """

    current_password = serializers.CharField(required=False)
    new_password = serializers.CharField()
    logout_other_sessions = serializers.BooleanField(default=False)

    def validate_new_password(self, value):
        """ Check password length """

        if AUTH_PASSWORD_LENGTH and len(value) < AUTH_PASSWORD_LENGTH:
            raise serializers.ValidationError(_('PASSWORD.INVALID'))
        return value


class ProfilePasswordClearSerializer(serializers.Serializer):
    """ Profile serializer for clearing an account password """
    pass
