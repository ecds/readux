##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from ipware import get_client_ip

class ProcessIpAddressMiddleware:
    """ Grap the IP address from the header """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.client_ip, request.is_routable = get_client_ip(request)
        response = self.get_response(request)
        return response
