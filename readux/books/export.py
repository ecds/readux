from django.conf import settings
import logging
import os
import shutil
import subprocess
import tempfile
from zipfile import ZipFile


logger = logging.getLogger(__name__)


# zip file of base jekyll site with digital edition templates
JEKYLL_THEME_ZIP = os.path.join(settings.BASE_DIR, 'readux', 'books',
    'fixtures', 'digitaledition-jekylltheme.zip')


class ExportException(Exception):
    pass


def website(vol, tei, static=True):
    '''Generate a zipfile of a jekyll website for a volume with annotations.
    Creates a jekyll site, imports pages and annotations from the TEI,
    and then packages it as a zipfile.

    :param vol: readux volume object (1.0 or 1.1)
    :param tei: annotated TEI facsimile (e.g.,
        :class:`~readux.books.tei.AnnotatedFacsimile`)
    :param static: if true, zip file contains the built jekyll site;
        otherwise, returns the full jekyll site.
    :return: :class:`tempfile.NamedTemporaryFile` temporary zip file
    '''
    logger.debug('Generating %s website for %s',
        'static' if static else 'jekyll', vol.pid)
    tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export')
    logger.debug('Building export for %s in %s', vol.pid, tmpdir)
    teifile = tempfile.NamedTemporaryFile(suffix='.xml', prefix='tei-',
        dir=tmpdir, delete=False)
    logger.debug('Saving TEI as %s', teifile.name)
    # write out tei to temporary file
    tei.serializeDocument(teifile)
    # IMPORTANT: close the filehandle to ensure *all* content is flushed
    # and available before running the ruby script
    teifile.close()
    # unzip jekyll template site
    logger.debug('Extracting jekyll template site')
    with ZipFile(JEKYLL_THEME_ZIP, 'r') as jekyllzip:
        jekyllzip.extractall(tmpdir)
    # run the script to import tei as jekyll site content
    jekyll_site_dir = os.path.join(tmpdir, 'digitaledition-jekylltheme-master')
    # run the jekyll import script in the jekyll site dir
    logger.debug('Running jekyll import TEI facsimile script')
    import_command = ['jekyllimport_teifacsimile', '-q', teifile.name]
    # when generating a site, configure jekyll site to generate relative links
    if static:
        import_command.append('--relative-links')
    try:
        subprocess.check_call(import_command, cwd=jekyll_site_dir)
    except subprocess.CalledProcessError:
        raise ExportException('Error importing TEI facsimile to jekyll site')

    # NOTE: putting export content in a separate dir to make it easy to create
    # the zip file with the right contents and structure
    export_dir = os.path.join(tmpdir, 'export')
    os.mkdir(export_dir)

    # if static website is requested, build the jekyll site and zip that up
    if static:
        # build the static jekyll site
        # run jekyll build from the jekyll site dir, output to build dir
        logger.debug('Building jekyll site')
        # directory where the built jekyll site will be put
        built_site_dir = os.path.join(export_dir, '%s_annotated_site' % vol.noid)
        try:
            subprocess.check_call(['jekyll', 'build', '-q', '-d', built_site_dir],
                cwd=jekyll_site_dir)
        except subprocess.CalledProcessError:
            raise ExportException('Error building jekyll site')

    # otherwise, zip up the entire (unbuilt) jekyll site
    else:
        # rename the jekyll dir and move it into our export dir
        shutil.move(jekyll_site_dir,
            os.path.join(export_dir, '%s_annotated_jekyll_site' % vol.noid))

    # create a tempfile to hold a zip file of the site
    # (using tempfile for automatic cleanup after use)
    webzipfile = tempfile.NamedTemporaryFile(suffix='.zip',
        prefix='%s_annotated_site_' % vol.noid)
    shutil.make_archive(os.path.splitext(webzipfile.name)[0],  # name of the zipfile to create without .zip
         'zip',  # archive format; could also do tar
         export_dir
        )
    logger.debug('%s web export zipfile for %s is %s',
        'Static' if static else 'Jekyll site', vol.pid, webzipfile.name)

    # clean up temporary files
    shutil.rmtree(tmpdir)
    # NOTE: method has to return the tempfile itself, or else it will get cleaned up when
    # the reference is destroyed
    return webzipfile