from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import View
from eulcommon.djangoextras.auth import login_required_with_ajax
from eulcommon.djangoextras.http.responses import HttpResponseSeeOtherRedirect

from readux.annotations.models import Annotation


class AnnotationIndex(View):

    def get(self, request):
        # TODO: include API links as per annotator 2.0 documentation
        return JsonResponse({
            "name": "Annotator Store API",
            "version": "2.0.0"
        })


non_ajax_error_msg = 'Currently Annotations can only be updated or created via AJAX.'

class Annotations(View):
    '''api/annotations

    On GET, lists annotations.
    On AJAX POST with json data in request body, creates a new
    annotation.'''

    def get(self, request):
        # NOTE: this method doesn't *technically* require annotations,
        # but under current permission model, no annotations should
        # be visible to anonymous users

        notes = Annotation.objects.all()
        # sort order?

        # superusers can view all annotations
        # other users can only see their own
        if not request.user.is_superuser:
            notes = notes.filter(user__username=request.user.username)

        # TODO: pagination; look at reference implementation
        return JsonResponse([n.info() for n in notes], safe=False)

    @method_decorator(login_required_with_ajax())
    def post(self, request):
        # for now, only support creation via ajax
        if request.is_ajax():
            note = Annotation.create_from_request(request)
            note.save()
            # annotator store documentation says to return 303
            # not sure why this isn't a 201 Created...
            return HttpResponseSeeOtherRedirect(note.get_absolute_url())

        else:
            return HttpResponseBadRequest(non_ajax_error_msg)


class AnnotationView(View):
    '''Views for displaying, updating, and removing a single Annotation.'''
    # TODO: check permissions for get/put/delete

    # all single-annotation views currently require user to be logged in
    @method_decorator(login_required_with_ajax())
    def dispatch(self, *args, **kwargs):
        return super(AnnotationView, self).dispatch(*args, **kwargs)

    def get_object(self):
        note = get_object_or_404(Annotation, id=self.kwargs.get('id', None))
        # check permissions: notes can only be viewed by superuser or not owner
        if not self.request.user.is_superuser and not self.request.user == note.user:
            raise PermissionDenied()
            # tpl = get_template('403.html')
            # return HttpResponseForbidden(tpl.render(RequestContext(request)))
            # return HttpResponseForbidden()
        return note

    def get(self, request, id):
        '''Display the JSON information for the requested annotation.'''
        # NOTE: if id is not a valid uuid this results in a ValueError
        # instead of a 404; should be handled by uuid regex in url config
        return JsonResponse(self.get_object().info())

    def put(self, request, id):
        '''Update the annotation via JSON data posted by AJAX.'''
        if request.is_ajax():
            note = self.get_object()
            note.update_from_request(request)
            return HttpResponseSeeOtherRedirect(note.get_absolute_url())
        else:
            return HttpResponseBadRequest(non_ajax_error_msg)

    # on DELETE, remove
    def delete(self, request, id):
        '''Remove the annotation.
        Returns a 204 No Content as per Annotator store API documentation.'''
        self.get_object().delete()
        response = HttpResponse('')
        # return 204 no content, according to annotator store api docs
        response.status_code = 204
        return response


class AnnotationSearch(View):

    def get(self, request):
        # TODO: what other search fields should be supported?

        notes = Annotation.objects.all()
        # For any user who is not a superuser, only provide
        # access to notes they own
        if not request.user.is_superuser:
            notes = notes.filter(user__username=request.user.username)

        uri = request.GET.get('uri', None)
        if uri is not None:
            notes = notes.filter(uri=uri)
        text = request.GET.get('text', None)
        if text is not None:
            notes = notes.filter(text__icontains=text)
        user = request.GET.get('user', None)
        if user is not None:
            notes = notes.filter(user__username=user)

        # minimal pagination: limit/offset
        limit = request.GET.get('limit', None)
        offset = request.GET.get('offset', None)
        # slice queryset by offset first, so limit will be relative to that
        if offset is not None:
            notes = notes[int(offset):]
        if limit is not None:
            notes = notes[:int(limit)]


        return JsonResponse({
            'total': notes.count(),
            'rows': [n.info() for n in notes]
        })