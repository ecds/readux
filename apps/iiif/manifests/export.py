from django.core.serializers import serialize
from .models import Manifest
from apps.iiif.annotations.models import Annotation
from apps.iiif.canvases.models import Canvas
from datetime import datetime
from apps.users.models import User
from apps.readux.models import UserAnnotation
import config.settings.local as settings
import digitaledition_jekylltheme
import io
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import zipfile


logger = logging.getLogger(__name__)

# zip file of base jekyll site with digital edition templates
JEKYLL_THEME_ZIP = digitaledition_jekylltheme.ZIPFILE_PATH
class ExportException(Exception):
    pass


class IiifManifestExport:
    @classmethod
    def get_zip(self, manifest, version, owners=[]):
        zip_subdir = manifest.label
        zip_filename = "iiif_export.zip"

        # Open BytesIO to grab in-memory ZIP contents
        byte_stream = io.BytesIO()

        # The zip compressor
        zf = zipfile.ZipFile(byte_stream, "w")

        # First write basic human-readable metadata
        ''' Annotated edition from {grab site identity/version of Readux} at {grab site URL}
        volume title
        volume author
        volume date
        volume publisher
        number of pages
        annotator username
        time of export
        '''
        title = manifest.label
        author = manifest.author
        date = manifest.published_date
        publisher = manifest.publisher
        page_count = manifest.canvas_set.count()
        now = datetime.utcnow()
        readux_url = settings.HOSTNAME
        annotators = User.objects.filter(userannotation__canvas__manifest__id=manifest.id).distinct()
        annotators_string = ', '.join([i.fullname() for i in annotators])
        # get the owner_id for each/all annotations
        # dedup the list of owners (although -- how to order?  alphabetical or by contribution count or ignore order)  .distinct()
        # turn the list of owners into a comma separated string of formal names instead of user ids
        readme = "Annotation export from Readux %(version)s at %(readux_url)s\nedition type: Readux IIIF Exported Edition\nexport date: %(now)s UTC\n\n" % locals()
        volume_data = "volume title: %(title)s\nvolume author: %(author)s\nvolume date: %(date)s\nvolume publisher: %(publisher)s\npages: %(page_count)s \n" % locals()
        annotators_attribution_string = "Annotated by: " + annotators_string +"\n\n"
        boilerplate = "Readux is a platform developed by Emory University’s Center for Digital Scholarship for browsing, annotating, and publishing with digitized books. This zip file includes an International Image Interoperability Framework (IIIF) manifest for the digitized book and an annotation list for each page that includes both the encoded text of the book and annotations created by the user who created this export. This bundle can be used to archive the recognized text and annotations for preservation and future access.\n\n"
        explanation = "Each canvas (\"sc:Canvas\") in the manifest represents a page of the work. Each canvas includes an \"otherContent\" field-set with information identifying that page's annotation lists. This field-set includes an \"@id\" field and the label field (\"@type\") \"sc:AnnotationList\" for each annotation list. The \"@id\" field contains the URL link at which the annotation list was created and originally hosted from the Readux site. In order to host this IIIF manifest and its annotation lists again to browse the book and annotations outside of Readux, these @id fields would need to be updated to the appropriate URLs for the annotation lists on the new host. Exported annotation lists replace nonword characters (where words are made up of alphanumerics and underscores) with underscores in the filename."
        readme = readme + volume_data + annotators_attribution_string + boilerplate + explanation
        zf.writestr('README.txt', readme)

        # Next write the manifest
        zf.writestr('manifest.json',
            json.dumps(
                json.loads(
                    serialize(
                        'manifest',
                        [manifest],
                        version=version,
                        annotators=User.objects.get(id__in=owners).name,
                        exportdate=now
                    )
                ),
                indent=4
            )
        )

        # Then write the OCR annotations
        for canvas in manifest.canvas_set.all():
            if canvas.annotation_set.count() > 0:
                json_hash = json.loads(
                  serialize(
                      'annotation_list',
                      [canvas],
                      version=version,
                      owners=owners
                  )
                )
                anno_uri = json_hash['@id']

                annotation_file = re.sub('\W','_', anno_uri) + ".json"

                zf.writestr(
                    annotation_file,
                    json.dumps(
                      json_hash,
                      indent=4
                    )
                )
        # Then write the user annotations
        for canvas in manifest.canvas_set.all():
            if canvas.userannotation_set.count() > 0:
                annotations = canvas.userannotation_set.filter(owner__in=owners).all()
                json_hash = json.loads(
                    serialize(
                        'user_annotation_list',
                        [canvas],
                        version=version,
                        is_list=False,
                        owners=[User.objects.get(id__in=owners)]
                    )
                )
                anno_uri = json_hash['@id']
                annotation_file = re.sub('\W','_', anno_uri) + ".json"

                zf.writestr(
                    annotation_file,
                    json.dumps(
                      json_hash,
                      indent=4
                    )
                )

        zf.close() # flush zipfile to byte stream

        return byte_stream.getvalue()


class JekyllSiteExport(object):
    def __init__(self, manifest, version, page_one=None, update_callback=None,
                 include_images=False, deep_zoom='hosted', github_repo=None, owners=None):
        # self.volume = volume
        self.manifest = manifest
        self.version = version
        # self.tei = tei
        # self.page_one = page_one
        self.update_callback = update_callback
        # self.include_images = include_images
        #self.deep_zoom = deep_zoom
        self.include_deep_zoom = (deep_zoom == 'include')
        self.no_deep_zoom = (deep_zoom == 'exclude')
        # self.github_repo = github_repo

        # # initialize github connection values to None
        # self.github = None
        # self.github_username = None
        # self.github_token = None
        self.jekyll_site_dir = None
        self.owners = owners


    def log_status(self, msg):
        logger.debug(msg)
        if self.update_callback is not None:
            self.update_callback(msg)

    def notify_msg(self, msg):
        log_status(msg)


    def get_zip(self):
        return self.volume_export()

    def iiif_dir(self):
        return os.path.join(self.jekyll_site_dir, 'iiif_export')

    def import_iiif_jekyll(self, manifest, tmpdir):
        # run the script to get a freash import of tei as jekyll site content
        self.log_status('Running jekyll import IIIF manifest script')
        # jekyllimport_tei_script = settings.JEKYLLIMPORT_TEI_SCRIPT
        jekyllimport_manifest_script = settings.JEKYLLIMPORT_MANIFEST_SCRIPT
        import_command = [jekyllimport_manifest_script, '--local-directory', '-q', self.iiif_dir(), tmpdir]
        # TODO
        # # if a page number is specified, pass it as a parameter to the script
        # if self.page_one is not None:
        #     import_command.extend(['--page-one', unicode(self.page_one)])
        # # if no deep zoom is requested, pass through so the jekyll
        # #  config can be updated appropriately
        if self.no_deep_zoom:
            import_command.append('--no-deep-zoom')

        try:
            logger.debug('Jekyll import command: %s', ' '.join(import_command))
            output = subprocess.check_output(' '.join(import_command), shell=True, stderr=subprocess.STDOUT)
            logger.debug('Jekyll import output:')
            logger.debug(output.decode('utf-8'))
#            subprocess.check_call(import_command, cwd=tmpdir)
        except subprocess.CalledProcessError as e:
            logger.debug('Jekyll import error:')
            logger.debug(e.output)
            err_msg = "Error running jekyll import on IIIF manifest!\n" + ' '.join(import_command) + "\n" + e.output.decode('utf-8')
            if self.update_callback is not None:
                self.update_callback(err_msg, 'error')
            raise ExportException(err_msg)



    def generate_website(self):
        """Generate a jekyll website for a volume with annotations.
        Creates a jekyll site and imports pages and annotations from the TEI,
        and then returns the directory for further use (e.g., packaging as
        a zipfile for download, or for creating a new GitHub repository).
        """
        logger.debug('Generating jekyll website for %s', self.manifest.id)
        tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export')
        logger.debug('Building export for %s in %s', self.manifest.id, tmpdir)

        # unzip jekyll template site
        self.log_status('Extracting jekyll template site')
        with zipfile.ZipFile(JEKYLL_THEME_ZIP, 'r') as jekyllzip:
            jekyllzip.extractall(tmpdir)
        self.jekyll_site_dir = os.path.join(tmpdir, 'digitaledition-jekylltheme')
        logger.debug('Jekyll site dir:')
        logger.debug(self.jekyll_site_dir)

        logger.debug('Exporting IIIF bundle')
        iiif_zip_stream = IiifManifestExport.get_zip(self.manifest, 'v2', owners=self.owners)
        iiif_zip = zipfile.ZipFile(io.BytesIO(iiif_zip_stream), "r")

        iiif_zip.extractall(self.iiif_dir())        



        # TODO
        # # save image files if requested, and update image paths in tei
        # # to use local references
        # if self.include_images:
        #     self.save_page_images(jekyll_site_dir)
        # if self.include_deep_zoom:
        #     self.generate_deep_zoom(jekyll_site_dir)


        # TODO -- equivalent to iiif zip export, which is probably unnecessary
        # teifile = self.save_tei_file(tmpdir)

        # run the script to import tei as jekyll site content
        self.import_iiif_jekyll(self.manifest, self.jekyll_site_dir)

        # NOTE: putting export content in a separate dir to make it easy to create
        # the zip file with the right contents and structure
        export_dir = os.path.join(tmpdir, 'export')
        os.mkdir(export_dir)

        # rename the jekyll dir and move it into the export dir
        shutil.move(self.jekyll_site_dir,
                    os.path.join(export_dir, '%s_annotated_jekyll_site' %
                                 self.manifest.id))

        return export_dir



    def website_zip(self):
        '''Package up a Jekyll site created by :meth:`website` as a zip file
        for easy download.

        :return: :class:`tempfile.NamedTemporaryFile` temporary zip file
        '''
        export_dir = self.generate_website()

        # create a tempfile to hold a zip file of the site
        # (using tempfile for automatic cleanup after use)
        webzipfile = tempfile.NamedTemporaryFile(
            suffix='.zip',
            prefix='%s_annotated_site_' % self.manifest.id)
        shutil.make_archive(
            # name of the zipfile to create without .zip
            os.path.splitext(webzipfile.name)[0],
            'zip',  # archive format; could also do tar
            export_dir
        )
        logger.debug('Jekyll site web export zipfile for %s is %s',
                     self.manifest.id, webzipfile.name)
        # clean up temporary files
        shutil.rmtree(export_dir)
        # NOTE: method has to return the tempfile itself, or else it will
        # get cleaned up when the reference is destroyed
        return webzipfile



# from readux/books/consumers.py in Readux 1.





    # This is essentially view code from readux 1's consumers.py, which parses
    # the export form, kicks off various exports, and handles S3 or Github 
    # integration.  It may need to be moved to the view for the initial pass.
    def volume_export(self, export_mode='download'):
    #     '''Consumer method to handle volume export form submission via
    #     websockets.  Initializes :class:`readux.books.export.VolumeExport`
    #     and then calls the appropriate method based on the requested export
    #     mode.
    #     '''

    #     username = message.content['user']
    #     user = get_user_model().objects.get(username=username)
    #     pid = message.content['formdata']['pid']
    #     # NOTE: for some reason, reply channel is not set on this message
    #     # using a group notification based on username rather than
    #     # relying on current websocket
    #     notify = Group(u"notify-%s" % user.username)

    #     def notify_msg(text, msg_type=None, **data):
    #         msg_data = {'message': text}
    #         if msg_type is not None:
    #             msg_data['type'] = msg_type
    #         msg_data.update(data)
    #         # breaking changes as of channels 1.0
    #         # need to specify immediately=True to send messages before the consumer completes to the end
    #         notify.send({'text': json.dumps(msg_data)}, immediately=True)

    #     notify_msg('Export started')

    #     user_has_github = False
    #     if not user.is_anonymous():
    #         # check if user has a github account linked
    #         try:
    #             github.GithubApi.github_account(user)
    #             user_has_github = True
    #         except github.GithubAccountNotFound:
    #             notify_msg(AnnotatedVolumeExport.github_account_msg, 'warning')

    #     export_form = VolumeExport(user, user_has_github,
    #                                message.content['formdata'])

    #     if not export_form.is_valid():
    #         notify_msg('Form is not valid; please modify and resubmit',
    #                    'error', form_errors=export_form.errors)
    #         logger.debug("Export form is not valid: %s", export_form.errors)
    #         # bail out
    #         return

    #     # if form is valid, then proceed with the export
    #     cleaned_data = export_form.cleaned_data
    #     export_mode = cleaned_data['mode']
    #     image_hosting = cleaned_data['image_hosting']
    #     include_images = (image_hosting == 'independently_hosted')
    #     deep_zoom = cleaned_data['deep_zoom']
    #     include_deep_zoom = (deep_zoom == 'include')
    #     no_deep_zoom = (deep_zoom == 'exclude')
    #     # This gets set below if exporting to GitHub.
    #     github_repo = None
    #     # deep zoom can't be included without including page images
    #     # this should be caught by form validation, but in case it isn't,
    #     # just assume include images is true if we get to this point
    #     if include_deep_zoom and not include_images:
    #         include_images = True

    #     # if github export or update is requested, make sure user
    #     # has a github account available to use for access
    #     # and add the repo name to the parameters
        # if export_mode in ['github', 'github_update']:
    #         try:
    #             github.GithubApi.github_account(user)
    #             github_repo = cleaned_data['github_repo']
    #         except github.GithubAccountNotFound:
    #             notify_msg(AnnotatedVolumeExport.github_account_msg, 'error')
    #             return

    #         # check that oauth token has sufficient permission
    #         # to do needed export steps
    #         gh = github.GithubApi.connect_as_user(user)
    #         # note: repo would also work here, but currently asking for public_repo
    #         if 'public_repo' not in gh.oauth_scopes():
    #             notify_msg(AnnotatedVolumeExport.github_scope_msg, 'error')
    #             return

    #     repo = Repository()
    #     vol = repo.get_object(pid, type=Volume)

    #     # determine which annotations should be loaded
    #     if cleaned_data['annotations'] == 'user':
    #         # annotations *by* this user
    #         # (NOT all annotations the user can view)
    #         annotations = vol.annotations().filter(user=user)
    #     elif cleaned_data['annotations'].startswith('group:'):
    #         # all annotations visible to a group this user belongs to
    #         group_id = cleaned_data['annotations'][len('group:'):]
    #         # NOTE: object not found error should not occur here,
    #         # because only valid group ids should be valid choices
    #         group = AnnotationGroup.objects.get(pk=group_id)
    #         annotations = vol.annotations().visible_to_group(group)

    #     notify_msg('Collected %d annotations' % annotations.count(),
    #                'status')
    #     # NOTE: could update message to indicate if using IIIF image urls
    #     notify_msg('Generating volume TEI', 'status')
    #     tei = vol.generate_volume_tei()
    #     notify_msg('Finished generating volume TEI', 'status')

    #     # if user requests images included, the image paths in the tei
    #     # need to be updated and the images need to be downloaded
    #     # to the local package (which doesn't exist yet...)
    #     if include_images:
    #         notify_msg('Updating image references in TEI', 'status')
    #         for i in range(len(tei.page_list)):
    #             teipage = tei.page_list[i]
    #             page = vol.pages[i]
    #             # convert from readux image url to
    #             # IIIF image url, so it can be downloaded and converted to
    #             # an image path local to the site
    #             for graphic in teipage.graphics:
    #                 # NOTE: some redundancy here with mode checks
    #                 # and modes in the page image view
    #                 if graphic.rend == 'full':
    #                     graphic.url = unicode(page.iiif)
    #                 elif graphic.rend == 'page':
    #                     graphic.url = unicode(page.iiif.page_size())
    #                 elif graphic.rend == 'thumbnail':
    #                     graphic.url = unicode(page.iiif.thumbnail())
    #                 elif graphic.rend == 'small-thumbnail':
    #                     graphic.url = unicode(page.iiif.mini_thumbnail())
    #                 elif graphic.rend == 'json':
    #                     graphic.url = unicode(page.iiif.info())

    #                 # TODO: canonicalize image urls *before* saving/referencing

        # generate annotated tei
    #     tei = annotate.annotated_tei(tei, annotations)
    #     notify_msg('Annotated TEI')

    #     exporter = export.VolumeExport(
    #         vol, tei, page_one=cleaned_data['page_one'],
    #         update_callback=notify_msg, include_images=include_images,
    #         deep_zoom=deep_zoom, github_repo=github_repo)

    #     # NOTE: passing in notify_msg method so that export methods
    #     # can also report on progress

    #     # exporting annotated tei only
        # if export_mode == 'tei':
    #         # reuse volume exporter logic to serialize the file to disk
    #         teifile = exporter.save_tei_file()
    #         # upload to temporary S3 bucket and send link to the user
    #         # - include username to avoid collisions with different users
    #         # exporting the same valume
    #         filename = '%s_annotated_tei_%s.xml' % (vol.noid, user.username)
    #         content_disposition = 'attachment;filename="%s"' % filename

    #         download_url = s3_upload(teifile.name, filename,
    #                                  content_disposition=content_disposition)
    #         notify_msg('TEI file available for download', 'status',
    #                    download_tei=True, download_url=download_url)

    #     # check form data to see if github repo is requested
        # elif export_mode == 'github':
    #         # create a new github repository with exported jekyll site
    #         try:
    #             repo_url, ghpages_url = exporter.website_gitrepo(
    #                 user, cleaned_data['github_repo'])

    #             logger.info('Exported %s to GitHub repo %s for user %s',
    #                         vol.pid, repo_url, user.username)

    #             # send success with urls to be displayed
    #             notify_msg('Export to GitHub complete', 'status',
    #                        github_export=True, repo_url=repo_url,
    #                        ghpages_url=ghpages_url)

    #         except export.GithubExportException as err:
    #             notify_msg('Export failed: %s' % err, 'error')

        # elif export_mode == 'github_update':
    #         # update an existing github repository with new branch and
    #         # a pull request
    #         try:
    #             pr_url = exporter.update_gitrepo(user, cleaned_data['update_repo'])

    #             notify_msg('GitHub jekyll site update completed', 'status',
    #                        github_update=True, pullrequest_url=pr_url,
    #                        repo_url=cleaned_data['update_repo'])

    #         except export.GithubExportException as err:
    #             notify_msg('Export failed: %s' % err, 'error')

        # elif export_mode == 'download':
            # non github export: download a jekyll site as a zipfile
#        try:
        webzipfile = self.website_zip()
    #             logger.info('Exported %s as jekyll zipfile for user %s',
    #                         vol.pid, user.username)
    #             notify_msg('Generated Jeyll zip file')

    #             # upload the generated zipfile to an Amazon S3 bucket configured
    #             # to auto-expire after 23 hours, so user can download
    #             notify_msg('Uploading zip file to Amazon S3')
    #             # include username in downlaod file label to avoid collisions
    #             label = '%s_annotated_jekyll_site_%s' % (vol.noid, user.username)
    #             download_url = s3_upload(webzipfile.name, label)

    #             notify_msg('Zip file available for download', 'status',
    #                        download=True, download_url=download_url)

    #         except export.ExportException as err:
    #             # display error to user
    #             notify_msg('Export failed: %s' % err, 'error')
        return webzipfile





