from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from eulcommon.djangoextras.http.responses import HttpResponseSeeOtherRedirect

from readux.annotations.models import Annotation

def root(request):
    # NOTE: would be convenient to include api links
    # similar to the reference implementation
    return JsonResponse({
      "name": "Annotator Store API",
      "version": "2.0.0"  # ??
    })


@csrf_exempt    # TEMPORARILY only
def annotations(request):
    # on GET, list annotations
    if request.method == 'GET':
        # TODO: pagination; look at reference implementation
        notes = Annotation.objects.all()
        # TODO: filter by permissions
        return JsonResponse([n.info() for n in notes], safe=False)

    # on POST, create new annotation
    if request.is_ajax() and request.method == 'POST':
        note = Annotation.create_from_request(request)
        note.save()
        # annotator store documentation says to return 303
        # not sure why this isn't a 201 Created...
        return HttpResponseSeeOtherRedirect(note.get_absolute_url())


@csrf_exempt    # TEMPORARILY only
def annotation(request, id):
    # NOTE: if id is not  a valid uuid this results in a ValueError
    # instead of a 404; should be handled by uuid regex in url config
    note = get_object_or_404(Annotation, id=id)

    # TODO: check permissions for get/put/delete

    # on GET, display
    if request.method == 'GET':
        return JsonResponse(note.info())

    # on PUT, update
    elif request.is_ajax() and request.method == 'PUT':
        note.update_from_request(request)
        return HttpResponseSeeOtherRedirect(note.get_absolute_url())

    # on DELETE, remove
    elif request.is_ajax() and request.method == 'DELETE':
        note.delete()
        response = HttpResponse('')
        # return 204 no content, according to annotator store api docs
        response.status_code = 204
        return response


def search(request):
    # TODO: what other search fields should be supported?
    # also TODO: limit/offset options for pagination
    uri = request.GET.get('uri', None)
    text = request.GET.get('text', None)
    notes = Annotation.objects.all()
    if uri is not None:
        notes = notes.filter(uri=uri)
    if text is not None:
        notes = notes.filter(text__icontains=text)
    return JsonResponse({
        'total': notes.count(),
        'rows': [n.info() for n in notes]
    })