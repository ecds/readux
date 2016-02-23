from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import json

from readux.annotations.models import Annotation

class Command(BaseCommand):
    '''Import a JSON file of annotation data in the format provided
    by the annotator store API (i.e., search results) and create
    corresponding local annotations for.
    '''

    def add_arguments(self, parser):
        parser.add_argument('file',
            help='JSON file with annotation data')

    def handle(self, *args, **options):
        print options['file']
        with open(options['file']) as datafile:
            data = json.loads(datafile.read())

        for annotation in data['rows']:
            self.import_annotation(annotation)

    def import_annotation(self, data):
        '''Create and save a new annotation, setting fields based on a
        dictionary of data passed in.  Raises an error if an annotation
        author is not found as a user in the database.'''
        note = Annotation()

        # NOTE: because we are using uuid for annotation id field,
        # importing an annotation twice does not error, but simply
        # replaces the old copy.  Might want to add checks for this...

        # required fields that should always be present
        # (not normally set by user)
        for field in ['updated', 'created', 'id']:
            setattr(note, field, data[field])
            del data[field]
        # user is special: annotation data only includes username,
        # but we need a user object
        # NOTE: this could result in making one person's annotations
        # available to someone else, if someone is using a different
        # username in another instance
        if 'user' in data:
            try:
                note.user = get_user_model().objects.get(username=data['user'])
                del data['user']
            except get_user_model().DoesNotExist:
                raise CommandError('Cannot import annotations for user %s (does not exist)' % data['user'])

        for field in Annotation.common_fields:
            if field in data:
                setattr(note, field, data[field])
                del data[field]

        # put any other data that is left in extra data json field
        if data:
            note.extra_data.update(data)

        note.save()
