##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from .utils import calculate_user_checksum


class ProfileSignatureMiddleware:
    """ Inserts profile checksum in http response headers """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = request.user
        if user and user.is_authenticated:
            response['Profile-Signature'] = calculate_user_checksum(user)
        return response
