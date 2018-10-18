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

User = get_user_model()


class EmailVerificationTestCase(TestCase):
    def setUp(self):
        self.data1 = {
            'email': '1@foo.com',
            'password': 'helloworldo',
        }
        self.user1 = User.objects.create_user(**self.data1)

    def test_verify_email_unauthenticated(self):
        verify_url = reverse(get_url_name(__name__, 'api-generics-email-exists'))
        resp = self.client.post(verify_url, {'email': self.user1.email})
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.json())
        self.assertTrue(resp.data['exists'], resp.json())

    def test_verify_email_unauthenticated_missing_params(self):
        verify_url = reverse(get_url_name(__name__, 'api-generics-email-exists'))
        resp = self.client.post(verify_url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, resp.json())

    def test_verify_email_authenticated(self):
        authenticated = self.client.login(username=self.data1['email'], password=self.data1['password'])
        self.assertTrue(authenticated)

        verify_url = reverse(get_url_name(__name__, 'api-generics-email-exists'))
        resp = self.client.post(verify_url, {'email': self.user1.email})
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.json())
        self.assertTrue(resp.data['exists'], resp.json())