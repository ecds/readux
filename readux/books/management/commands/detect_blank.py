import logging

from readux.books.management.page_import import BasePageImport


logger = logging.getLogger(__name__)


class Command(BasePageImport):
    '''Utility script to check if an image or images would be identified as
    blank using the same logic as import_covers and import_pages scripts.

    Takes a list of image file paths.'''
    help = __doc__

    def handle(self, *images, **options):

        self.setup(**options)


        for imgfile in images:
            try:
                blank = self.is_blank_page(imgfile)
                print '%s is%s blank' % (imgfile, '' if blank else ' not')
            except:
                print 'Error reading %s' % imgfile
