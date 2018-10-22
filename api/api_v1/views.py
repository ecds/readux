##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy
from rest_framework import permissions

from .utils.common import get_url_name


@api_view(('GET',))
@permission_classes((permissions.AllowAny,))
def api_root(request, format=None):
    api_root = {
        'profiles': reverse_lazy(
            get_url_name(__name__, 'api-profile-list'),
            request=request,
            format=format,
        ),
    }
    return Response(api_root)


class CfgTestView(TemplateView):
    """
    A mixin that can be used to render a JSON response.
    """
    def render_to_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(self.get_data(context), safe=False, **response_kwargs)

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        data = {
            'id': self.request.user.id,
            'name': 'foo',
            'group': 'bar',
            'total': 10
        }
        return data

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
