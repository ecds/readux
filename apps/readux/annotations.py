from django.core.serializers import serialize
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView
from .models import UserAnnotation
from ..iiif.canvases.models import Canvas
import json
import uuid

class Annotations(ListView):

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return UserAnnotation.objects.filter(
                owner=self.request.user,
                canvas=Canvas.objects.get(pid=self.kwargs['canvas'])
            )
        return None

    def get(self, request, *args, **kwargs):
        annotations = self.get_queryset()
        if annotations is not None:
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
        return JsonResponse(status=200, data={})

class AnnotationCrud(View):

    def dispatch(self, request, *args, **kwargs):
        # Don't do anything if no user is authenticated.
        if hasattr(request, 'user') is False or request.user.is_authenticated is False:
            return self.__unauthorized()
        
        # Get the payload from the request body.
        self.payload = json.loads(self.request.body.decode('utf-8'))
        return super(AnnotationCrud, self).dispatch(request, *args, **kwargs)   

    def get_queryset(self):
        try:
            return UserAnnotation.objects.get(
                pk=self.payload['id'],
                owner=self.request.user
            )
        except UserAnnotation.DoesNotExist:
            return None

    def post(self, request):
        oa_annotation = json.loads(self.payload['oa_annotation'])
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

    def put(self, request):
        # if hasattr(request, 'user') is False or request.user.is_authenticated is False:
        #     return self.__unauthorized()

        # self.payload = json.loads(request.body.decode('utf-8'))
        annotation = self.get_queryset()

        if annotation is None:
            return self.__not_found()

        elif hasattr(request, 'user') and annotation.owner == request.user:
            annotation.oa_annotation = self.payload['oa_annotation']
            annotation.save()
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
        else:
            return self.__unauthorized()

    def delete(self, request):

        annotation = self.get_queryset()

        if annotation is None:
            return self.__not_found()
        elif annotation.owner == request.user:
            annotation.delete()
            return JsonResponse({}, status=204)
        else:
            return self.__unauthorized()

    def __not_found(self):
        return JsonResponse({'message': 'Annotation not found.'}, status=404)

    def __unauthorized(self):
        return JsonResponse({'message': 'You are not the owner of this annotation.'}, status=401)
