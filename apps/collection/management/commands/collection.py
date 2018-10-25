import sys
import json
import codecs
import logging
import requests
import hashlib
from pprint import pprint
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from toolware.utils.generic import get_uuid
from utils.fetch import rate_limited, fetch_url
from ...models import Collection
from ... import defaults as defs

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetches collections from iiif api"

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--fetch',
            action='store_true',
            dest='fetch',
            default=False,
            help='Fetch collections from the IIIF endpoint'
        )

        parser.add_argument(
            '-d',
            '--depth',
            action='store',
            dest='depth',
            type=int,
            default=1,
            help='Fetch sub collections of depth of <n>'
        )

        parser.add_argument(
            '-l',
            '--load',
            action='store_true',
            dest='load',
            default=False,
            help='Fetch and load data to db'
        )

        parser.add_argument(
            '-o',
            '--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help='For update if data exists in db'
        )

        parser.add_argument(
            '-s',
            '--save',
            action='store_true',
            dest='save',
            default=False,
            help='Fetch and save to local json file'
        )

        parser.add_argument(
            '-p',
            '--print',
            action='store_true',
            dest='print',
            default=False,
            help='Fetch and print to screen'
        )

    def handle(self, *args, **options):
        """ Handles command """
        self.verbosity = options['verbosity']
        self.fetch = options['fetch']
        self.load = options['load']
        self.overwrite = options['overwrite']
        self.depth = options['depth']
        self.save = options['save']
        self.print = options['print']

        if not self.fetch:
            self.print_help("", subcommand='collection')
            return

        if self.depth > defs.MAX_SUB_COLLECTIONS_DEPTH:
            self.stdout.write('Depth exceeding the max of {}'.format(self.MAX_SUB_COLLECTIONS_DEPTH))
            return

        self.created = 0
        self.updated = 0
        self.process(defs.IIIF_UNIVERSE_COLLECTION_URL, 0)
        if self.verbosity > 2:
            sys.stdout.write('Created collections: ({})\n'.format(self.created))
            sys.stdout.write('Updated collections: ({})\n'.format(self.updated))

    def process(self, url, depth):
        """ Fetch and process url """
        if self.verbosity > 2:
            self.stdout.write('Preparing to fetch collections ... ({})'.format(url))

        data = self.fetch_collection(url, defs.HTTP_REQUEST_TIMEOUT, format='json')
        if not data:
            self.stdout.write('Failed to fetch collections ...')
            return

        if self.print:
            pprint(data)
        
        if self.save:
            self.dump_json_to_file('dev_iiif_{}.json'.format(get_uuid(16)), data)

        identification = data.get('@id')
        if not identification:
            if self.verbosity >2:
                sys.stdout.write('Failed to fetch collection for ({})\n'.format(url))
            return

        instance = self.create_or_update(data, depth)
        collections_data = data.get('collections')
        if not collections_data:
            if self.verbosity >=3:
                sys.stdout.write('Not sub collections for ({})\n'.format(identification))
            return

        self.proccess_children(instance, collections_data, depth+1)

    def proccess_children(self, parent, collections_data, depth):
        """ Process sub collections """
        for child in collections_data:
            instance = self.create_or_update(child, depth)
            if instance:
                parent.children.add(instance)
            if depth < self.depth:
                self.process(instance.identification, depth)
    
    def create_or_update(self, data, depth):
        """ Given a dict of collection attributes, it creates or updates an instance. """

        default_data = {
            'identification': data.get('@id'),
            'context': data.get('@context'),
            'type': data.get('@type'),
            'label': data.get('label'),
            'logo': data.get('logo'),
            'description': data.get('description'),
            'attribution': data.get('attribution'),
            'depth': depth,
        }

        instance, created = Collection.objects.get_or_create_unique(default_data, ['identification', 'depth'])
        if not instance:
            if self.verbosity >2:
                sys.stdout.write('Failed to create collection for ({})\n'.format(identification))
            return

        if created:
            self.created += 1

        if not created and self.overwrite:
            for attr, value in defaults.items():
                if getattr(instance, attr):
                    setattr(instance, attr, value)
            instance.save()
            self.updated += 1

        return instance

    @rate_limited(defs.API_CALLS_LIMIT_PER_SECONDS)
    def fetch_collection(self, url, timeout, format):
        """ Fetch from API while throttling our calls """
        resp = fetch_url(url, timeout=timeout, format=format)
        return resp

    def dump_json_to_file(self, file_name, content):
        """ Flush content to local file """
        with open(file_name, 'w') as outfile:
            json.dump(
                content,
                outfile,
                sort_keys=True,
                indent=2,
                ensure_ascii=False
            )
