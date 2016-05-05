from collections import OrderedDict
import json
import logging
import uuid
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group, User
from django.utils.html import format_html
from jsonfield import JSONField
from guardian.shortcuts import assign_perm, get_perms_for_model
from guardian.models import UserObjectPermission, GroupObjectPermission


logger = logging.getLogger(__name__)


class AnnotationQuerySet(models.QuerySet):
    'Custom :class:`~django.models.QuerySet` for :class:`Annotation`'

    def visible_to(self, user):
        '''Restrict to annotations the specified user is allowed to access.
        Currently, superusers can view all annotations; all other users
        can access only their own annotations.'''
        # currently, superusers can view all annotations;
        # other users can only see their own
        if not user.is_superuser:
            return self.filter(user__username=user.username)
        return self.all()

    def last_created_time(self):
        '''Creation time of the most recently created annotation. If
        queryset is empty, returns None.'''
        try:
            return self.values_list('created', flat=True).latest('created')
        except Annotation.DoesNotExist:
            pass

    def last_updated_time(self):
        '''Update time of the most recently created annotation. If
        queryset is empty, returns None.'''
        try:
            return self.values_list('created', flat=True).latest('created')
        except Annotation.DoesNotExist:
            pass


class AnnotationManager(models.Manager):
    '''Custom :class:`~django.models.Manager` for :class:`Annotation`.
    Returns :class:`AnnotationQuerySet` as default queryset, and exposes
    :meth:`visible_to` for convenience.'''

    def get_queryset(self):
        return AnnotationQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        'Convenience access to :meth:`AnnotationQuerySet.visible_to`'
        return self.get_queryset().visible_to(user)


class Annotation(models.Model):
    '''Django database model to store Annotator.js annotation data,
    based on the
    `annotation format documentation <http://docs.annotatorjs.org/en/v1.2.x/annotation-format.html>`_.'''

    #: regex for recognizing valid UUID, for use in site urls
    UUID_REGEX = r'[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'

    #: annotation schema version: default v1.0
    schema_version = "v1.0"
    # for now, hard-coding until or unless we need to support more than
    # one version of annotation

    #: unique id for the annotation; uses :meth:`uuid.uuid4`
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # data model includes version, do we need to set that in the db?
    # "annotator_schema_version": "v1.0",        # schema version: default v1.0

    #: datetime annotation was created; automatically set when added
    created = models.DateTimeField(auto_now_add=True)
    #: datetime annotation was last updated; automatically updated on save
    updated = models.DateTimeField(auto_now=True)
    #: content of the annotation
    text = models.TextField()
    #: the annotated text
    quote = models.TextField()
    #: URI of the annotated document
    uri = models.URLField()
    #: user who owns the annotation
    #: when serialized, id of annotation owner OR an object with an 'id' property
    # Make user optional for now
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

    #: Readux-specific field: URI for the volume that an annotation
    #: is associated with (i.e., volume a page is part of)
    volume_uri = models.URLField(blank=True)

    # tags still todo
    # "tags": [ "review", "error" ],             # list of tags (from Tags plugin)

    #: any additional data included in the annotation not parsed into
    #: specific model fields; this includes ranges, permissions,
    #: annotation data, etc
    extra_data = JSONField(default=json.dumps({}))
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

    #: fields in the db model that are provided by annotation json
    #: when creating or updating an annotation
    common_fields = ['text', 'quote', 'uri', 'user', 'volume_uri']
    # NOTE: volume_uri is not strictly a 'common' field, since it would
    # just be extra data to any other annotator backend, but we
    # need it stored for searching and querying.

    objects = AnnotationManager()

    class Meta:
        # extend default permissions to add a view option
        # change_annotation and delete_annotation provided by django
        permissions = (
            ('view_annotation', 'View annotation'),
            ('admin_annotation', 'Manage annotation'),
        )

    def __unicode__(self):
        return self.text

    def __repr__(self):
        return '<Annotation: %s>' % self.text

    def get_absolute_url(self):
        'URL to view this annotation within the annotation API.'
        return reverse('annotation-api:view', kwargs={'id': self.id})

    def text_preview(self):
        'Short preview of annotation text content'
        return self.text[:100] + ('...' if len(self.text) > 100 else '')
    text_preview.short_description = 'Text'

    def uri_link(self):
        'URI as a clickable link'
        return format_html('<a href="{}">{}</a>', self.uri, self.uri)
    uri_link.short_description = 'URI'

    @property
    def related_pages(self):
        'convenience access to list of related pages in extra data'
        if 'related_pages' in self.extra_data:
            return self.extra_data['related_pages']

    @classmethod
    def create_from_request(cls, request):
        '''Initialize a new :class:`Annotation` based on data from a
        :class:`django.http.HttpRequest`.

        Expects request body content to be JSON; sets annotation user
        based on the request user.
        '''

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
        '''Update attributes from data in a
        :class:`django.http.HttpRequest`. Expects request body content to be
        JSON.   Currently does *not* modify user.'''
        data = json.loads(request.body)
        # NOTE: could keep a list of modified fields and
        # and allow Django to do a more efficient db update

        # ignore backend-generated fields, and don't include in
        # the extra data
        # NOTE: assuming for now that user should NOT be changed
        # after annotation is created
        for field in ['updated', 'created', 'id', 'user']:
            try:
                del data[field]
            except KeyError:
                pass

        # set any db fields, and remove from extra data
        for field in self.common_fields:
            if field in data:
                setattr(self, field, data[field])
                del data[field]

        # if permissions are specified, convert into actionable django
        # permissions and remove from the data
        if 'permissions' in data:
            self.db_permissions(data['permissions'])
            del data['permissions']

        if data:
            # any other data included in the request and not yet
            # processed should be stored as extra data
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
            # tags handled as part of extra data
        ])
        # There shouldn't be collisions between extra data and db
        # fields, but in case there are, none of the extra data shoudl
        # override core fields
        info.update({k: v for k, v in self.extra_data.iteritems()
                     if k not in info})

        # annotation permissions dict based on database permissions
        permissions = self.permissions_dict()
        # only include if at least one permission is not empty
        if any(permissions.values()):
            info['permissions'] = permissions

        # volume uri would be extra data to anyone else, but since it
        # is stored outside extra data, add it here
        if self.volume_uri:
            info['volume_uri'] = self.volume_uri

        return info

    #: map annotator permissions to django annotation permission codenames
    permission_to_codename = {
        'read': 'view_annotation',
        'update': 'change_annotation',
        'delete': 'delete_annotation',
        'admin': 'admin_annotation'
    }
    #: lookup annotation permission mode by django permission codename
    codename_to_permission = dict([(codename, mode) for mode, codename
                                   in permission_to_codename.iteritems()])

    def user_permissions(self):
        '''Queryset of :class:`guardian.model.UserObjectPermission`
        objects associated with this annotation.'''
        return UserObjectPermission.objects.filter(object_pk=self.pk)

    def group_permissions(self):
        '''Queryset of :class:`guardian.model.GroupObjectPermission`
        objects associated with this annotation.'''
        return GroupObjectPermission.objects.filter(object_pk=self.pk)

    def get_group_or_user(self, ident):
        # look up annotation group or user based on username
        # or group id in annotation permissions list
        if ident.startswith('group:'):
            group_id = ident[len('group:'):]
            try:
                return AnnotationGroup.objects.get(id=int(group_id))
            except ValueError:
                # non-integer identifier found
                logger.warn("Invalid group id '%s' in annotation %s permissions",
                            group_id, self.pk)
            except AnnotationGroup.DoesNotExist:
                logger.warn("Error finding group '%s' in annotation %s permissions",
                            group_id, self.pk)
        else:
            try:
                return User.objects.get(username=ident)
            except User.DoesNotExist:
                logger.warn("Error finding user '%s' in annotation %s permissions",
                            ident, self.pk)

    def db_permissions(self, permissions):
        '''Convert annotation permission data into actionable
        django permissions using :mod:`guardian` per-object permissions.
        '''
        # since there is no way to know what permissions were
        # previously in place and need to be removed, remove all permissions
        self.user_permissions().delete()
        self.group_permissions().delete()

        # NOTE: should eventually handle special case
        # group:__world__, but setting that is currently not supported
        # by the readux annotator permissions module

        # then re-assign permissions based on annotation permissions
        for mode, users in permissions.iteritems():
            for ident in users:
                entity = self.get_group_or_user(ident)
                if entity is not None:
                    print 'mode is ', mode
                    print 'codename is ', self.permission_to_codename[mode]
                    # give user/group the appropriate permission on this object
                    assign_perm(self.permission_to_codename[mode],
                                entity, self)

    def permissions_dict(self):
        '''Convert stored :mod:`guardian` per-object permissions into
        annotation permission dictionary format'''
        # convert db permissions into annotator style permissions

        # construct base permissions dict, empty list for each mode
        permissions = dict([(mode, [])
                           for mode in self.permission_to_codename.keys()])

        for user_perm in self.user_permissions():
            # convert db codename to annotation mode
            mode = self.codename_to_permission[user_perm.permission.codename]
            # store by username
            permissions[mode].append(user_perm.user.username)

        for group_perm in self.group_permissions():
            mode = self.codename_to_permission[group_perm.permission.codename]
            permissions[mode].append(group_perm.group.annotationgroup.annotation_id)

        return permissions


class AnnotationGroup(Group):
    # inherits name from Group

    #: optional notes field
    notes = models.TextField(blank=True)
    #: datetime annotation was created; automatically set when added
    created = models.DateTimeField(auto_now_add=True)
    #: datetime annotation was last updated; automatically updated on save
    updated = models.DateTimeField(auto_now=True)

    def num_members(self):
        return self.user_set.count()
    num_members.short_description = '# members'

    def __repr__(self):
        return '<Annotation Group: %s>' % self.name

    @property
    def annotation_id(self):
        return 'group:%d' % self.pk
