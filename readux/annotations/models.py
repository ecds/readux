from collections import OrderedDict
import json
import uuid
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from jsonfield import JSONField


class Annotation(models.Model):
    '''AnnotatorJS annotation model, based on the documentation at
    http://docs.annotatorjs.org/en/v1.2.x/annotation-format.html.'''

    #: regex for recognizing valid UUID, for use in urls
    UUID_REGEX = r'[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'

    #: schema version: default v1.0
    schema_version = "v1.0"
    # for now, hard-coding until or unless we need to support more than
    # one version of annotation

    #: unique id (added by backend)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # data model includes version, do we need to set that in the db?
    # "annotator_schema_version": "v1.0",        # schema version: default v1.0

    #: created datetime; serialize in iso8601 format (added by backend)
    created = models.DateTimeField(auto_now_add=True)
    #: updated datetime in iso8601 format (added by backend)
    updated = models.DateTimeField(auto_now=True)
    #: content of the annotation
    text = models.TextField()
    #: the annotated text (added by frontend)
    quote = models.TextField()
    #: URI of annotated document (added by frontend)
    uri = models.URLField()
    #: user who owns the annotation
    #: when serialized, id of annotation owner OR an object with an 'id' property
    # Make user optional for now
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

    # tags still todo
    # "tags": [ "review", "error" ],             # list of tags (from Tags plugin)


    #: any additional data included in the annotation not parsed into
    #: specific model fields; this includes ranges, permissions,
    #: annotation data, etc
    extra_data = JSONField()
    # example range from the documentation
    # "ranges": [
    #     {
    #        "start": "/p[69]/span/span",           # (relative) XPath to start element
    #        "end": "/p[70]/span/span",             # (relative) XPath to end element
    #        "startOffset": 0,                      # character offset within start element
    #        "endOffset": 120                       # character offset within end element
    #    }
    # ]
    # example permissions from the documentation
    # "permissions": {
    #     "read": ["group:__world__"],
    #     "admin": [],
    #     "update": [],
    #     "delete": []
    # }

    # NOTE: according to the documentation, the basic schema is
    # extensible, can be added to by plugins, and any fields added by the
    # frontend should be preserved by the backend.  Store any of that
    # additional information in the extra_data field.

    #: db model fields provided by annotation json
    common_fields = ['text', 'quote', 'uri', 'user']


    def __unicode__(self):
        return self.text

    def __repr__(self):
        return '<Annotation: %s>' % self.text

    def get_absolute_url(self):
        return reverse('annotation-api:view', kwargs={'id': self.id})

    @classmethod
    def create_from_request(cls, request):
        '''Initialize a new :class:`Annotation` based on data from a
        :class:`django.http.HttpRequest`.'''
        # still TODO: set annotation user based on request.user
        data = json.loads(request.body)


        model_data = {}
        extra_data = {}
        for k, v in data.iteritems():
            if k in Annotation.common_fields:
                model_data[k] = v
            else:
                extra_data[k] = v

        if not request.user.is_anonymous():
            model_data['user'] = request.user

        # convert extra data back to json for storage in a single json field
        return cls(extra_data=json.dumps(extra_data), **model_data)


    def update_from_request(self, request):
        '''Update attributes from data in a :class:`django.http.HttpRequest`.'''
        data = json.loads(request.body)
        # NOTE: could keep a list of modified fields and
        # and allow Django to do a more efficient db update
        for field in self.common_fields:
            # ignore backend-generated fields, but don't include in
            # the extra data
            # NOTE: assuming for now that user should NOT be changed
            # after annotation is created
            if field in ['updated', 'created', 'id', 'user'] \
              and field in data:

                del data[field]
                continue

            if field in data:
                setattr(self, field, data[field])
                del data[field]

        if data:
            # add/update extra data json with any other data included
            # in the request
            self.extra_data.update(data)

        self.save()

    def info(self):
        '''Return a :class:`collections.OrderedDict` of fields to be
        included in serialized JSON version of the current annotation.'''
        info = OrderedDict([
            ('id', unicode(self.id)),
            ('annotator_schema_version', self.schema_version),
            # iso8601 formatted dates
            ('created', self.created.isoformat() if self.created else ''),
            ('updated', self.updated.isoformat() if self.updated else ''),
            ('text', self.text),
            ('quote', self.quote),
            ('uri', self.uri),
            ('user', self.user.username if self.user else ''),
            # tags TODO
        ])
        # There shouldn't be collisions between extra data and db
        # fields, but in case there are, none of the extra data shoudl
        # override core fields
        info.update({k: v for k, v in self.extra_data.iteritems()
                     if k not in info})
        return info
