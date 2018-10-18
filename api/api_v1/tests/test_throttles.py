##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

import json
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status

from ..utils.common import get_url_name
from ..utils.throttles import ProfileCreateRateThrottle


User = get_user_model()


class ProfileCreateThrottleOnePerDayTestCase(TestCase):
    def setUp(self):
        from django.conf import settings
        settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['profile_create'] = '1/day'
        self.url = reverse(get_url_name(__name__, 'api-profile-create'))

    def test_create_one_per_day(self):
        """
        Allow one request per day per IP.
        """
        resp = self.client.post(self.url, {'email': '1@foo.com', 'password': 'helloworldo'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.post(self.url, {'email': '2@foo.com', 'password': 'helloworldo'})
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class ProfileCreateThrottleTwoPerDayTestCase(TestCase):
    def setUp(self):
        from django.conf import settings
        settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['profile_create'] = '3/day'
        self.url = reverse(get_url_name(__name__, 'api-profile-create'))

    def test_create_two_per_day_success(self):
        resp = self.client.post(self.url, {'email': '1@foo.com', 'password': 'helloworldo'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.post(self.url, {'email': '2@foo.com', 'password': 'helloworldo'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
