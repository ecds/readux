
'''
import volume manage Command

assume single volume only, and not in the repo (onus on user to check for now)

takes one option, should be path to bag with book/volume contents

- check that the bag is valid
- identify required files in the bag
- construct and ingest book object
- construct and ingest volume object

report on what was done
'''
import bagit
from lxml.etree import XMLSyntaxError
from optparse import make_option
import os

from django.core.management.base import BaseCommand, CommandError
from eulfedora.server import RequestFailed
from eulxml.xmlmap import load_xmlobject_from_file
from eulxml.xmlmap.dc import DublinCore

from readux.fedora import ManagementRepository
from readux.books.models import Book, VolumeV1_1


class Command(BaseCommand):
    '''Import a single volume into the repository for display in Readux.'''
    help = __doc__

    args = ' <path>'
    # TODO: arg for collection id

    def handle(self, *paths, **options):

        if not len(paths):
            raise CommandError('Please specify path to content for import.')
        if len(paths) > 1:
            # this limitation is kind of arbitrary, but keep thing simple for now
            raise CommandError('Import currently only supports a single volume.')
        path = paths[0]

        # should collection be required? maybe for now?
        # TODO: check collection pid is set and exists as a collection

        try:
            bag = bagit.Bag(path)
            # NOTE: could consider using fast validation, but files probably are
            # not so large or so numerous that this will be an issue
            bag.validate()
        except bagit.BagError as err:
            raise CommandError('Please supply a valid BagIt as input. %s' % err)
        except bagit.ValidationError as err:
            raise CommandError('Input is not a valid bag. %s' % err)

        files = {'pdf': None, 'marcxml': None, 'dc': None}
        checksums = {}

        # identify required contents within the bag by extension and name
        for data_path in bag.payload_files():
            # path is relative to bag root dir
            filename = os.path.join(path, data_path)

            # get extension and name
            basename = os.path.basename(filename)
            basefile, ext = os.path.splitext(basename)
            # NOTE: splitext leaves . on the ext portion

            if ext.lower() == '.pdf':
                files['pdf'] = filename
                checksums['pdf'] = bag.entries[data_path].get('md5', None)

            elif ext.lower() == '.xml':

                if basefile.lower() == 'marc':
                    files['marcxml'] = filename
                    checksums['marcxml'] = bag.entries[data_path].get('md5', None)

                elif basefile.lower() == 'dc':
                    files['dc'] = filename
                    checksums['dc'] = bag.entries[data_path].get('md5', None)

        # check that required components are present
        err = False
        for label, path in files.iteritems():
            if path is None:
                self.stderr.write('%s not found' % label.upper())
                err = True

            elif checksums[label] is None:
                self.stderr.write('No MD5 checksum found for %s' % label.upper())
                err = True

        if err:
            raise CommandError('Cannot import without all required files and checksums.')

        # all pieces are available, so proceed with ingest
        repo = ManagementRepository()

        # construct book and ingest
        try:
            marcxml = load_xmlobject_from_file(files['marcxml'])
        except XMLSyntaxError as err:
            raise CommandError('Failed to load %s as xml: %s' % (files['marcxml'], err))
        try:
            dcxml = load_xmlobject_from_file(files['dc'], DublinCore)
        except XMLSyntaxError as err:
            raise CommandError('Failed to load %s as xml: %s' % (files['dc'], err))

        book = repo.get_object(type=Book)
        # TODO: set label (to what?)
        # TODO: associate with collection
        book.marcxml.content = marcxml
        book.marcxml.checksum = checksums['marcxml']
        book.dc.content = dcxml
        # NOTE: import checksum can't be used because DC is modified to add ARK
        # book.dc.checksum = checksums['dc']

        # save; bail if error
        try:
            saved = book.save('ingest')
            if not saved:
                raise CommandError('Failed to ingest book into repository')
        except RequestFailed as err:
            raise CommandError('Error ingesting book: %s' % err)


        # construct volume (v1.1), associate with book, and ingest
        with open(files['pdf']) as pdf_file:
            vol = repo.get_object(type=VolumeV1_1)
            vol.pdf.content = pdf_file
            vol.pdf.checksum = checksums['pdf']
            # TODO: object label ?
            # TODO: minimal DC metadata derived from book ?
            vol.book = book
            # TODO: fedora error handling
            saved = vol.save('ingest')

        if not saved:
            raise CommandError('Failed to ingest volume into repository')

        self.stdout.write('Successfully ingested book %s and volume %s' % \
            (book.pid, vol.pid))







