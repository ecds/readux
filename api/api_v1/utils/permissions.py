##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.contrib.auth import get_user_model

from rest_framework import permissions

User = get_user_model()


class IsOwner(permissions.BasePermission):
    """
    Custom permission: read: owner, write: owner
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, User):
            obj.user = obj
        return obj.user.id == request.user.id


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission: read: all, write: owner
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, User):
            obj.user = obj
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user.id == request.user.id


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission: read: owner | staff, write: owner | staff
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, User):
            obj.user = obj
        return obj.user == request.user or request.user.is_staff


class IsNotAuthenticated(permissions.IsAuthenticated):
    """
    Custom permission: read,write: unauthenticated users
    """
    def has_permission(self, request, view, obj=None):
        if request.user and request.user.is_authenticated:
            return False
        else:
            return True
