##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

import logging

from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model

from rest_framework import views
from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from ..utils.throttles import BurstRateThrottle
from ..utils.throttles import SustainedRateThrottle

from .serializers import *

User = get_user_model()
log = logging.getLogger(__name__)


class GenericsVerifyEmailAPIView(views.APIView):
    """ Verify if email is in use """
    permission_classes = (AllowAny,)
    throttle_classes = (BurstRateThrottle, SustainedRateThrottle,)

    def post(self, request, format=None):
        email = request.data.get('email')
        if email:
            if User.objects.filter(email__iexact=email).exists():
                return Response({'exists': True, 'details': _('EMAIL.IN_USE')})
            else:
                return Response({'exists': False, 'details': _('EMAIL.NOT_IN_USE')})
        return Response({'status': _('ERROR.MISSING_PARAMS'.format(__param__='email')), 'errno': 'ERROR.MISSING_PARAMS'}, status=status.HTTP_400_BAD_REQUEST)
