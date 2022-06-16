"""Django Views for USER Annotations."""
from __future__ import annotations
import json
import uuid
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize, deserialize
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView
from django.contrib.auth import get_user_model
from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.models import Manifest
from .models import UserAnnotation

USER = get_user_model()

class Annotations(ListView):
    """
    Display a list of UserAnnotations for a specific user.
    :rtype: json
    """
    def get_queryset(self):
        return Canvas.objects.filter(pid=self.kwargs['canvas'])

    def get(self, request, *args, **kwargs):
        username = kwargs['username']
        try:
            owner = USER.objects.get(username=username)
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
            return JsonResponse(
                status=401,
                data={"Permission to see annotations not allowed for logged in account.": username}
            )

        except ObjectDoesNotExist:
            return JsonResponse(status=404, data={"USER not found.": username})

class WebAnnotations(ListView):
    """
    Display a list of UserAnnotations for a specific user.
    :rtype: json
    """
    def get_queryset(self):
        return Canvas.objects.filter(pid=self.kwargs['canvas'])

    def get(self, request, *args, **kwargs):
        username = kwargs['username']
        try:
            query_set = self.get_queryset()
            owner = USER.objects.get(username=username)
            if self.request.user == owner:
                return JsonResponse(
                    json.loads(
                        serialize(
                            'annotation_page_v3',
                            query_set,
                            annotations=query_set.first().userannotation_set.filter(owner=owner)
                        )
                    ),
                    safe=False
                )
            return JsonResponse(
                status=401,
                data={"Permission to see annotations not allowed for logged in account.": username}
            )

        except ObjectDoesNotExist:
            return JsonResponse(status=404, data={"USER not found.": username})



class AnnotationCrud(View):
    """Endpoint for User Annotation CRUD."""
    def dispatch(self, request, *args, **kwargs):
        # Don't do anything if no user is authenticated.
        if hasattr(request, 'user') is False or request.user.is_authenticated is False:
            return self.__unauthorized()

        # Get the payload from the request body.
        self.payload = json.loads(self.request.body.decode('utf-8'))
        return super(AnnotationCrud, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Fetch requested :class:`apps.readux.models.UserAnnotation`

        :rtype: :class:`django.db.models.QuerySet`
        """
        try:
            return UserAnnotation.objects.get(
                pk=self.payload['id']
            )
        except UserAnnotation.DoesNotExist:
            return None

    def post(self, request):
        """HTTP POST endpoint for creating annotations.

        :return: Newly created annotation as IIIF Annotation.
        :rtype: json
        """
        annotation = None
        if 'oa_annotation' in self.payload:
            annotation = UserAnnotation()
            oa_annotation = json.loads(self.payload['oa_annotation'])
            annotation.oa_annotation = oa_annotation
            annotation.owner = request.user
            annotation.motivation = 'oa:commenting'
            annotation.save()
        else:
            deserialized_annotation, tags = deserialize('annotation_v3', self.payload)
            annotation = UserAnnotation(**deserialized_annotation)
            annotation.save()
            annotation.refresh_from_db()
            for tag in tags:
                annotation.tags.add(tag)
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
        """HTTP PUT endpoint for updating annotations.

        :return: Updated IIIF Annotation
        :rtype: json
        """
        # if hasattr(request, 'user') is False or request.user.is_authenticated is False:
        #     return self.__unauthorized()

        # self.payload = json.loads(request.body.decode('utf-8'))
        annotation = self.get_queryset()

        if annotation is None:
            return self.__not_found()

        elif hasattr(request, 'user') and annotation.owner == request.user:
            if 'oa_annotation' in self.payload:
                annotation.oa_annotation = self.payload['oa_annotation']
            else:
                updated_annotation, tags = deserialize('annotation_v3', self.payload)
                annotation.update(updated_annotation, tags)

            annotation.refresh_from_db()

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
