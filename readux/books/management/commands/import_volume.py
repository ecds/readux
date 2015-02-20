
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
import time

from django.core.management.base import BaseCommand, CommandError
from eulfedora.server import RequestFailed
from eulxml.xmlmap import load_xmlobject_from_file, load_xmlobject_from_string
from eulxml.xmlmap.dc import DublinCore

from readux.fedora import ManagementRepository
from readux.books.models import Book, VolumeV1_1, MinMarcxml, PageV1_1
from readux.collection.models import Collection


class Command(BaseCommand):
    '''Import a single volume into the repository for display in Readux.'''
    help = __doc__

    args = ' <path>'
    option_list = BaseCommand.option_list + (
        make_option('--collection', '-c',
            help='Associate the new volume with the specified collection.'),
        make_option('--dry-run', '-n',
            action='store_true',
            default=False,
            help='Don\'t make any changes; just report on what would be done'),
        make_option('--fast-validate', '-f',
            action='store_true',
            default=False,
            help='Bagit fast validation (skip checking all checksums at bag load time)')
    )

    #: default verbosity level
    v_normal = 1

    def handle(self, *paths, **options):

        if not len(paths):
            raise CommandError('Please specify path to content for import.')
        if len(paths) > 1:
            # this limitation is kind of arbitrary, but keep thing simple for now
            raise CommandError('Import currently only supports a single volume.')
        path = paths[0]

        dry_run = options.get('dry_run', False)
        verbosity = options.get('verbosity', self.v_normal)

        repo = ManagementRepository()

        # make collection required to avoid accidentally forgetting it
        coll = options.get('collection', None)
        if coll is None:
            raise CommandError('Please specify collection pid')

        collection = repo.get_object(coll, type=Collection)
        if not collection.exists:
            raise CommandError('Collection %s does not exist' % coll)
        if not collection.has_requisite_content_models:
            raise CommandError('%s is not a collection' % coll)

        try:
            start = time.time()
            bag = bagit.Bag(path)
            # NOTE: could consider using fast validation, but files probably are
            # not so large or so numerous that this will be an issue
            if verbosity > self.v_normal:
                self.stdout.write('Validating bag %s' % path)
            fast_validate = options.get('fast_validate')
            bag.validate(fast=fast_validate)
            if verbosity >= self.v_normal:
                self.stdout.write('Validated %s in %.02fs %s' % (path, time.time() - start,
                    '(fast validation enabled)' if fast_validate else ''))
        except bagit.BagError as err:
            # failed to load directory as a bag
            raise CommandError('Please supply a valid BagIt as input. %s' % err)
        except bagit.BagValidationError as err:
            # bag is not valid
            raise CommandError('Input is not a valid bag. %s' % err)

        files = {'pdf': None, 'marcxml': None, 'dc': None}
        checksums = {}

        # this is potentially a long list, but go ahead and store since we will
        # be consulting it multiple times
        payload_files = list(bag.payload_files())

        # identify required contents within the bag by extension and name
        for data_path in payload_files:
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
        for label, filepath in files.iteritems():
            if filepath is None:
                self.stderr.write('%s not found' % label.upper())
                err = True

            elif checksums[label] is None:
                self.stderr.write('No MD5 checksum found for %s' % label.upper())
                err = True

        if err:
            raise CommandError('Cannot import without all required files and checksums.')

        # all pieces are available, so proceed with ingest


        # construct book and ingest
        if verbosity > self.v_normal:
            self.stdout.write('Creating book object with marxml %s' % files['marcxml'])
        try:
            marcxml = load_xmlobject_from_file(files['marcxml'], MinMarcxml)
        except XMLSyntaxError as err:
            raise CommandError('Failed to load %s as xml: %s' % (files['marcxml'], err))
        try:
            dcxml = load_xmlobject_from_file(files['dc'], DublinCore)
        except XMLSyntaxError as err:
            raise CommandError('Failed to load %s as xml: %s' % (files['dc'], err))

        # look for book by ocm number first, in case a previous ingest failed
        book_pids = Book.pids_by_label(marcxml.ocm_number)
        # error if we find more than one
        if len(book_pids) > 1:
            raise CommandError('Multiple books exist with label %s. Please correct this first.' \
                                % marcxml.ocm_number)

        # if we find exactly one, use that instead of creating a new book
        elif len(book_pids) == 1:
            book = repo.get_object(book_pids[0], type=Book)
            if verbosity >= self.v_normal:
                self.stdout.write('Using existing book %s with ocm number %s' % \
                    (book.pid, marcxml.ocm_number))

        # otherwise, ingest new book
        else:
            book = repo.get_object(type=Book)
            # set book label to ocm number from the marc
            book.label = marcxml.ocm_number
            if verbosity > self.v_normal:
                self.stdout.write('Book label %s' % book.label)

            # associate with collection
            if collection is not None:
                book.collection = collection
                if verbosity > self.v_normal:
                    self.stdout.write('Associating with collection %s' % collection.short_label)
            book.marcxml.content = marcxml
            # NOTE: import checksum can't be used because xml may be serialized differently
            # book.marcxml.checksum = checksums['marcxml']
            book.dc.content = dcxml
            # NOTE: import checksum can't be used because DC is modified to add ARK
            # book.dc.checksum = checksums['dc']

            # save; bail if error
            if not dry_run:
                try:
                    saved = book.save('ingest')
                    if not saved:
                        raise CommandError('Failed to ingest book into repository')
                    if verbosity >= self.v_normal:
                        self.stdout.write('Successfully ingested book %s' \
                                    % book.pid)
                except RequestFailed as err:
                    raise CommandError('Error ingesting book: %s' % err)

        # in case of pre-existing book object, check for existing volume
        if book.volume_set:
            if len(book.volume_set) > 1:
                raise CommandError('Book %s has multiple volumes; import not supported' \
                    % book.pid)
            else:
                # use existing volume object
                vol = book.volume_set[0]
                if verbosity >= self.v_normal:
                    self.stdout.write('Using existing volume %s' % vol.pid)

        # otherwise, create new volume object
        else:
            # construct volume (v1.1), associate with book, and ingest
            if verbosity > self.v_normal:
                self.stdout.write('Creating volume with %s' % files['pdf'])
            with open(files['pdf']) as pdf_file:
                vol = repo.get_object(type=VolumeV1_1)
                # set volume label to ocm number from the marc + volume number
                # for consistency with lsdi content, use ocm_v# notation
                # V.0 indicates single-volume book
                vol.label = '%s_V.0' % marcxml.ocm_number
                # set pdf content
                vol.pdf.content = pdf_file
                vol.pdf.checksum = checksums['pdf']
                # set relation to parent book object
                vol.book = book
                # minimal DC metadata derived from book metadata
                vol.dc.content.title = book.dc.content.title
                for t in book.dc.content.type_list:
                    vol.dc.content.type_list.append(t)
                vol.dc.content.format = book.dc.content.format
                vol.dc.content.language = book.dc.content.language
                vol.dc.content.rights = book.dc.content.rights

                if not dry_run:
                    try:
                        saved = vol.save('ingest')
                        if not saved:
                            # NOTE: possibly, if this fails, we should deactivate the book object
                            # but will leave that to manual processing for now
                            raise CommandError('Failed to ingest volume into repository')
                        else:
                            if verbosity >= self.v_normal:
                                self.stdout.write('Successfully ingested volume %s' \
                                    % vol.pid)
                    except RequestFailed as err:
                        raise CommandError('Error ingesting volume: %s' % err)


        #### page import

        # if volume has existing pages, bail
        if len(vol.pages):
            raise CommandError('Volume %s already has %s page%s' % \
                (vol.pid, len(vol.pages), '' if len(vol.pages) == 1 else 's'))

        # should page import happen here?
        # - identify numeric jp2/jpf files in the bag and get total count
        # - identify numeric .xml files in the bag and get total count
        # - make sure counts match up
        # Question: can we assume no start/end blank pages for now?
        # - start looping through, create page-1.1 and associate with book,
        #   and ingest
        # - set first page as primary image on the volume
        # - report number of pages ingested

        image_files = []

        # identify page files (images and ocr xml)
        for data_path in payload_files:
            # get extension and name
            basename = os.path.basename(data_path)
            basefile, ext = os.path.splitext(basename)
            if ext in ['.jp2', '.jpf']:
                image_files.append(data_path)
                # check that MD5 is present and bail if not
                # - this is probably redundant since by this point validation
                # has passed and previous content has checksums, but
                # ingest will assume checksums are available so better to error
                # *before* starting to ingest page-level content
                if bag.entries[data_path].get('md5', None) is None:
                    raise CommandError('No MD5 checksum for %s' % data_path)

        # ensure pages are sorted into page-order
        image_files.sort()

        # NOTE: disabled for now; tunebook does not appear to include alto
        # for pages with no text content
        ## find matching page ocr files
        # for imgfile in image_files:
        #     basefile, ext = os.path.splitext(imgfile)
        #     ocrfile = '%s.xml' % basefile
        #     if ocrfile not in payload_files:
        #         raise CommandError('No OCR xml page present for %s (expected %s)' % \
        #             (imgfile, ocrfile))

        # pre-generate empty xml in case we need it to force eulfedora to not
        # create ocr datastream when no ocr is present
        emptyxml = load_xmlobject_from_string('<empty/>')

        # iterate through page images and put into fedora
        pageindex = 1
        for imgfile in image_files:
            if verbosity > self.v_normal:
                print 'Creating Page object for %s' % imgfile
            # path is relative to bag root dir
            img_filename = os.path.join(path, imgfile)

            with open(img_filename) as img_content:
                page = repo.get_object(type=PageV1_1)
                # set page label
                page.label = '%s page %d' % (vol.label, pageindex)
                # set the relation to the volume object
                page.volume = vol
                # set a dc:title based on volume title
                page.dc.content.title = '%s page %d' % (vol.dc.content.title, pageindex)
                # set page order
                page.page_order = pageindex

                # set image content
                page.image.content = img_content
                page.image.checksum = bag.entries[imgfile]['md5']
                # assume jpeg2000 for now (only looking for jp2/jpf)
                page.image.mimetype = 'image/jp2'

                # check for ocr xml within the bag, same base name as image
                basefile, ext = os.path.splitext(imgfile)
                ocrfile = '%s.xml' % basefile

                if ocrfile in payload_files:
                    page.ocr.content = load_xmlobject_from_file(os.path.join(path, ocrfile))
                    # NOTE: can't use MD5 from bag because XML may be
                    # serialized differently when sent to Fedora
                    # (unless we treat as file instead of xml...)
                    # page.ocr.checksum = bag.entries[ocrfile]['md5']

                    if verbosity > self.v_normal:
                        print 'Setting OCR for Page from %s' % ocrfile

                else:
                    # warn but do not error if ocr xml is not found
                    self.stdout.write('Warning: no OCR xml found for %s' % imgfile)
                    # explicitly set xml content to empty so eulfedora doesn't
                    # attempt to bootstrap & ingest (and error)
                    page.ocr.content = emptyxml

                if not dry_run:
                    try:
                        # for now, if any page ingest errors, bail out
                        # (unclear what would cause load to fail midway)

                        saved = page.save()


                        if not saved:
                            raise CommandError('Failed to ingest page %d into repository' \
                                % pageindex)

                    except RequestFailed as err:
                        raise CommandError('Error ingesting page %d: %s' % (pageindex, err))

            # set first page as primary image for the volume
            if not dry_run and pageindex == 1:
                vol.primary_image = page
                vol.save('adding primary image relation')

            # increase page index for next page
            pageindex += 1

        if verbosity >= self.v_normal:
            # total is pageindex - 1 since pageindex incremented at end of loop
            self.stdout.write('Created %d pages' % (pageindex - 1))



