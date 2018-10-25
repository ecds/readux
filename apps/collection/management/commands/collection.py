import sys
import json
import codecs
import logging
import requests
from pprint import pprint
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from ... import defaults as defs
from utils.fetch import rate_limited, fetch_url

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

        parser.add_argument(
            '-d',
            '--depth',
            action='store',
            dest='depth',
            type=int,
            default=2,
            help='Fetch sub collections of depth of <n>'
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

        self.process()

    def process(self, url=defs.IIIF_UNIVERSE_COLLECTION_URL):
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
            self.dump_json_to_file('dev_iiif.json', data)

        return data

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
