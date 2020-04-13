from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView
from django.contrib.auth import get_user_model
from .models import UserAnnotation
from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.models import Manifest
import json
import uuid

User = get_user_model()

class Annotations(ListView):
    """
    Display a list of UserAnnotations for a specific user.
    Returns
    -------
    json
    """
    def get_queryset(self):
        return Canvas.objects.filter(pid=self.kwargs['canvas'])

    def get(self, request, *args, **kwargs):
        username = kwargs['username']
        try:
            owner = User.objects.get(username=username)
            if self.request.user == owner:
                return JsonResponse(
                    json.loads(
                        serialize(
                            'user_annotation_list',
                            self.get_queryset(),
                            owners=[owner]
                        )
                    ),
                    safe=False
                )
            return JsonResponse(status=401, data={"Permission to see annotations not allowed for logged in user.": username})

        except ObjectDoesNotExist:
            # attempt to get annotations for non-existent user
            return JsonResponse(status=404, data={"User not found.": username})
        # return JsonResponse(status=200, data={})


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
                pk=self.payload['id']
            )
        except UserAnnotation.DoesNotExist:
            return None

    def post(self, request):
        oa_annotation = json.loads(self.payload['oa_annotation'])
        annotation = UserAnnotation()
        annotation.oa_annotation = oa_annotation
        annotation.owner = request.user
        annotation.motivation = 'oa:commenting'
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
                status=200
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
