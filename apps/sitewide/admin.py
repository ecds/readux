##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.contrib import admin
from django.contrib.sessions.models import Session
from django.contrib.auth.models import Permission


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    def _session_data(self, obj):
        return obj.get_decoded()
    list_display = ['expire_date', '_session_data', 'session_key']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    pass
