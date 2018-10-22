##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from rest_framework.response import Response
from rest_framework import decorators
from rest_framework import viewsets
from rest_framework import status
from rest_framework import mixins
from rest_framework import generics
from rest_framework import views
from rest_framework import filters

from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated

from ..utils.permissions import IsOwner
from ..utils.permissions import IsNotAuthenticated
from ..utils.throttles import BurstRateThrottle
from ..utils.throttles import SustainedRateThrottle
from ..utils.throttles import ProfileCreateRateThrottle

from .serializers import *

log = logging.getLogger(__name__)
User = get_user_model()


class ProfileFilter():
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']


class ProfileViewMixin(object):
    serializer_class = ProfileReadAnonymousSerializer
    permission_classes = (IsAuthenticated, IsOwner,)
    throttle_classes = (BurstRateThrottle, SustainedRateThrottle,)

    def get_serializer_class(self):
        if self.request.method == "GET":
            if self.request.user.is_authenticated:
                return ProfileReadAuthenticatedSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = User.objects.all()
        if self.request.method == "GET":
            if not self.request.user.is_superuser:
                return queryset.filter(is_active=True, is_superuser=False)
            if not self.request.user.is_staff:
                return queryset.filter(is_active=True, is_superuser=False, is_staff=False)
        return queryset


class ProfileListAPIView(ProfileViewMixin, generics.ListAPIView):
    """ Profile List View """

    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = [
        'email',
        'first_name',
        'last_name',
    ]
    ordering_fields = [
        'id',
        'email',
        'first_name',
        'last_name',
        'last_login',
        'created_at',
    ]


class ProfileRetrieveAPIView(ProfileViewMixin, generics.RetrieveAPIView):
    """ Profile Retrieve View """

    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if self.lookup_field not in self.kwargs:
            if self.lookup_field == 'pk':
                self.kwargs[self.lookup_field] = self.request.user.id
            else:
                self.kwargs[self.lookup_field] = getattr(self.request.user, self.lookup_field, None)
        return self.retrieve(request, *args, **kwargs)


class ProfileCreateAPIView(ProfileRetrieveAPIView, generics.CreateAPIView):
    """ Profile Create View """

    serializer_class = ProfileCreateSerializer
    permission_classes = (IsNotAuthenticated,)
    throttle_classes = (ProfileCreateRateThrottle,)

    def perform_create(self, serializer):
        if serializer.is_valid():
            password = serializer.validated_data['password']
            instance = serializer.save()
            if instance:
                instance.set_password(password)
                instance.save()


class ProfileUpdateAPIView(ProfileRetrieveAPIView, generics.UpdateAPIView):
    """ Profile Update View """

    serializer_class = ProfileUpdateSerializer
    permission_classes = (IsAuthenticated, IsOwner,)


class ProfileDeleteAPIView(ProfileRetrieveAPIView, generics.DestroyAPIView):
    """ Profile Delete View """

    permission_classes = (IsAuthenticated, IsOwner,)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.is_superuser:
            #  Cannot delete privileged user via api.
            return Response({'status': _('USER.DELETE.NOT_ALLOWED')}, status.HTTP_403_FORBIDDEN)
        return super(ProfileDeleteAPIView, self).destroy(request, *args, **kwargs)


class ProfilePasswordChangeAPIView(ProfileRetrieveAPIView, generics.GenericAPIView):
    """ Profile Password Change View """

    def get_serializer_class(self):
        if self.request.method == "GET":
            if self.request.user.is_authenticated:
                return ProfileReadAuthenticatedSerializer
        return ProfilePasswordChangeSerializer

    def post(self, request, format=None):
        user = request.user
        serializer = ProfilePasswordChangeSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        current_password = serializer.data.get('current_password')
        if current_password is None or len(current_password) == 0:
            if user.has_usable_password():  # hint: social registration perhaps?
                return Response({'current_password': _('PASSWORD.INVALID')},
                    status.HTTP_400_BAD_REQUEST)

        elif not user.check_password(current_password):
            return Response({'current_password': _('PASSWORD.INVALID')},
                    status.HTTP_400_BAD_REQUEST)

        new_password = serializer.data.get('new_password')
        if user.check_password(new_password):
            return Response({'new_password': _('PASSWORD.TOO_SIMILAR')},
                status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'status': _('PASSWORD.CHANGED')})
