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


def static_website(vol):
    tei = vol.generate_volume_tei()
    tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export')
    logger.debug('Building export for %s in %s', vol.pid, tmpdir)
    teifile = tempfile.NamedTemporaryFile(suffix='.xml', prefix='tei-',
        dir=tmpdir)
    logger.debug('Saving TEI as %s', teifile.name)
    # write out tei to temporary file
    tei.serializeDocument(teifile)
    # unzip jekyll template site
    logger.debug('Extracting jekyll template site')
    with ZipFile(JEKYLL_THEME_ZIP, 'r') as jekyllzip:
        jekyllzip.extractall(tmpdir)
    # run the script to import tei as jekyll site content
    jekyll_site_dir = os.path.join(tmpdir, 'digitaledition-jekylltheme-master')
    # run the jekyll import script in the jekyll site dir
    logger.debug('Running jekyll import TEI facsimile script')
    subprocess.call(['jekyllimport_teifacsimile', '-q', teifile.name],
        cwd=jekyll_site_dir)
    # check for return val == 0 ?

    # build the static jekyll site
    # NOTE: creating built site in a separate dir to make it easy to create
    # the zip file with the right contents and structure
    build_dir = os.path.join(tmpdir, 'build')
    os.mkdir(build_dir)
    # run jekyll build from the jekyll site dir, output to build dir
    logger.debug('Building jekyll site')
    # directory where the built jekyll site will be put
    built_site_dir = os.path.join(build_dir, '%s_annotated_site' % vol.noid)
    subprocess.call(['jekyll', 'build', '-q', '-d', built_site_dir],
        cwd=jekyll_site_dir)
    # tempfile to create a zip file of the built site
    # (using tempfile for automatic cleanup after use)
    webzipfile = tempfile.NamedTemporaryFile(suffix='.zip',
        prefix='%s_annotated_site_' % vol.noid)
    shutil.make_archive(os.path.splitext(webzipfile.name)[0],  # name of the zipfile to create without .zip
         'zip',  # archive format; could also do tar
         build_dir
        )
    logger.debug('Static web export zipfile for %s is %s', vol.pid, webzipfile.name)
    # clean up temporary files
    del teifile  # tempfile cleans up on deletion, complains if it's already gone
    shutil.rmtree(tmpdir)
    # NOTE: method has to return the tempfile itself, or else it will get cleaned up when
    # the reference is destroyed
    return webzipfile