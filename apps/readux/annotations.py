from django.core.serializers import serialize
from django.http import JsonResponse
from django.views import View
# from django.contrib.auth.models import User
# from django.contrib.auth import get_user_model
from django.views.generic import ListView
from .models import UserAnnotation
from ..iiif.canvases.models import Canvas
# from ..iiif.serializers import AnnotationSerializer
import json

class Annotations(ListView):

    def get_queryset(self):
        return UserAnnotation.objects.filter(
            owner=self.request.user,
            canvas=Canvas.objects.get(pid=self.kwargs['canvas'])
        )

    def get(self, request, *args, **kwargs):
        annotations = self.get_queryset()
        for anno in annotations:
        return JsonResponse(
            json.loads(
                serialize(
                    'annotation',
                    annotations,
                    # version=kwargs['version'],
                    is_list = True
                )
            ),
            safe=False,
            status=200
        )

    def post(self, request):
        payload = json.loads(request.body.decode('utf-8'))
        oa_annotation = json.loads(payload['oa_annotation'])
        annotation = UserAnnotation()
        annotation.oa_annotation = oa_annotation
        annotation.owner = request.user
        annotation.save()
        # TODO: should we respond with the saved annotation?
        return JsonResponse(
            json.loads(
                serialize(
                    'annotation',
                    [annotation]
                )
            ),
            safe=False,
            status=201
        )

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['user_annotations'] = UserAnnotation.objects.filter(
    #         user=User.objects.get(username=self.request.user),
    #         canvas=Canvas.objects.get(pid=self.kwargs['canvas'])
    #     )
    #     return context
