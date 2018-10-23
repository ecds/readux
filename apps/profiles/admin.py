##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django import forms
from django.contrib import admin
from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.sites import NotRegistered
from django.utils.translation import ugettext_lazy as _

from .models import Profile


@admin.register(Profile)
class UserProfileAdmin(UserAdmin):
    fieldsets = (
        # Translators: admin
        (_('USER.FIELDS.REQUIRED'), {'fields': ('email', 'password')}),
        # Translators: admin
        (_('USER.FIELDS.PERSONAL'), {'fields': ('first_name', 'last_name')}),
        # Translators: admin
        (_('USER.FIELDS.PERMISSIONS'), {'fields': ('status', 'is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        # Translators: admin
        (_('USER.FIELDS.DATES'), {'fields': ('last_login', 'created_at')}),
        # Translators: admin
        (_('USER.FIELDS.MISC'), {'fields': ('photo', 'language', )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('id', 'email', 'first_name', 'last_name', 'language', 'is_active', 'is_verified', 'is_staff', 'is_superuser', 'created_at', 'last_login',)
    list_filter = ('is_staff', 'is_superuser', 'is_active',)
    search_fields = ('first_name', 'last_name', 'email',)
    ordering = ('email',)
    filter_horizontal = ('user_permissions',)
